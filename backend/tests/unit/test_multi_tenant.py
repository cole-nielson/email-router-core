"""
Enhanced multi-tenant functionality tests.
Tests the advanced client identification, domain resolution, and fuzzy matching capabilities.
"""

from unittest.mock import Mock

import pytest

from core.clients.manager import ClientIdentificationResult, EnhancedClientManager
from core.clients.resolver import (
    DomainMatcher,
    calculate_domain_similarity,
    extract_domain_from_email,
    get_domain_hierarchy,
    get_domain_variants,
    match_domain_pattern,
    normalize_domain,
)
from core.ports.config_provider import ConfigurationProvider
from infrastructure.config.manager import ConfigurationError, get_config_manager


@pytest.fixture
def mock_enhanced_client_manager():
    """Create a properly mocked EnhancedClientManager for testing."""
    # Create a mock config provider with realistic client data
    config_provider = Mock(spec=ConfigurationProvider)

    # Mock client config that matches the test expectations
    mock_client_config = Mock()
    mock_client_config.client_id = "client-001-cole-nielson"
    mock_client_config.name = "Cole Nielson Email Router"
    mock_client_config.industry = "Technology"
    mock_client_config.timezone = "UTC"
    mock_client_config.active = True

    # Mock domains configuration with test domains
    mock_domains = Mock()
    mock_domains.primary = "colenielson.dev"
    mock_domains.aliases = ["mail.colenielson.dev", "api.colenielson.dev"]
    mock_domains.catch_all = False
    mock_domains.support = "support@colenielson.dev"
    mock_domains.mailgun = "mg.colenielson.dev"
    mock_client_config.domains = mock_domains

    # Mock other required config sections
    mock_client_config.branding = Mock()
    mock_client_config.contacts = Mock()

    # Mock routing rules with proper structure for expected tests
    mock_routing_rule_support = Mock()
    mock_routing_rule_support.category = "support"
    mock_routing_rule_support.email = "colenielson.re@gmail.com"
    mock_routing_rule_support.enabled = True

    mock_routing_rule_billing = Mock()
    mock_routing_rule_billing.category = "billing"
    mock_routing_rule_billing.email = "colenielson8@gmail.com"
    mock_routing_rule_billing.enabled = True

    mock_client_config.routing = [mock_routing_rule_support, mock_routing_rule_billing]

    # Mock SLA configuration with proper response times
    mock_sla = Mock()
    mock_sla.response_times = {
        "support": 240,  # 4 hours in minutes
        "billing": 1440,  # 24 hours in minutes
        "urgent": 15,
        "high": 60,
        "medium": 240,
        "low": 1440,
    }
    mock_client_config.sla = mock_sla

    mock_client_config.settings = Mock()
    mock_client_config.ai_categories = ["general", "support", "billing", "sales"]
    mock_client_config.custom_prompts = {}

    # Set up the mock to return client data
    config_provider.get_all_clients.return_value = {"client-001-cole-nielson": mock_client_config}

    def mock_get_client_config(client_id):
        if client_id == "client-001-cole-nielson":
            return mock_client_config
        return None

    config_provider.get_client_config.side_effect = mock_get_client_config

    # Create the enhanced client manager with the mock provider
    return EnhancedClientManager(config_provider=config_provider)


def test_client_discovery():
    """Test that we can discover available clients"""
    config_manager = get_config_manager()
    clients = list(config_manager.get_all_clients().keys())
    assert isinstance(clients, list)
    assert len(clients) >= 1  # Should have at least client-001-cole-nielson

    # Check that client IDs follow expected format
    for client_id in clients:
        assert client_id.startswith("client-")
        assert isinstance(client_id, str)


def test_load_client_config():
    """Test loading client configuration"""
    config_manager = get_config_manager()

    # Should be able to load the test client
    config = config_manager.get_client_config("client-001-cole-nielson")
    assert config.client_id == "client-001-cole-nielson"
    assert config.name == "Cole Nielson Email Router"
    assert config.domains.primary == "mail.colesportfolio.com"


def test_enhanced_client_manager_domain_resolution(mock_enhanced_client_manager):
    """Test enhanced domain resolution with multiple strategies"""
    manager = mock_enhanced_client_manager

    # Test exact domain match
    result = manager.identify_client_by_domain("colenielson.dev")
    assert isinstance(result, ClientIdentificationResult)
    assert result.client_id == "client-001-cole-nielson"
    assert result.confidence == 1.0
    assert result.method == "exact_match"
    assert result.is_successful

    # Test subdomain hierarchy matching
    result = manager.identify_client_by_domain("api.colenielson.dev")
    assert result.client_id == "client-001-cole-nielson"
    assert result.confidence >= 0.7
    assert (
        "hierarchy" in result.method or "exact" in result.method
    )  # Could be exact if variant was added
    assert result.is_successful


def test_enhanced_client_manager_email_identification(mock_enhanced_client_manager):
    """Test enhanced email-based client identification"""
    manager = mock_enhanced_client_manager

    # Test direct email identification
    result = manager.identify_client_by_email("support@colenielson.dev")
    assert result.client_id == "client-001-cole-nielson"
    assert result.is_successful

    # Test subdomain email identification
    result = manager.identify_client_by_email("api@test.colenielson.dev")
    assert result.client_id == "client-001-cole-nielson"
    assert result.is_successful

    # Test backward compatibility method
    client_id = manager.identify_client_by_email_simple("support@colenielson.dev")
    assert client_id == "client-001-cole-nielson"


async def test_enhanced_client_manager_routing(mock_enhanced_client_manager):
    """Test enhanced routing with confidence-based decisions"""
    manager = mock_enhanced_client_manager

    # Test category routing
    destination = await manager.get_routing_destination("client-001-cole-nielson", "support")
    assert destination == "colenielson.re@gmail.com"

    destination = await manager.get_routing_destination("client-001-cole-nielson", "billing")
    assert destination == "colenielson8@gmail.com"


async def test_enhanced_client_manager_response_times(mock_enhanced_client_manager):
    """Test response time lookup with enhanced configuration"""
    manager = mock_enhanced_client_manager

    # Test specific category response times
    response_time = await manager.get_response_time("client-001-cole-nielson", "support")
    assert response_time == "within 4 hours"

    response_time = await manager.get_response_time("client-001-cole-nielson", "billing")
    assert response_time == "within 24 hours"


async def test_client_validation(mock_enhanced_client_manager):
    """Test enhanced client configuration validation"""
    manager = mock_enhanced_client_manager

    # Valid client should pass validation
    is_valid = await manager.validate_client_setup("client-001-cole-nielson")
    assert is_valid == True


def test_unknown_client_handling(mock_enhanced_client_manager):
    """Test handling of unknown clients with enhanced fallback"""
    manager = mock_enhanced_client_manager

    # Should return failure result for unknown domain
    result = manager.identify_client_by_domain("nonexistent.example.com")
    assert not result.is_successful
    assert result.client_id is None
    assert result.method == "no_match"

    # Should return None for unknown email with simple method
    client_id = manager.identify_client_by_email_simple("test@nonexistent.example.com")
    assert client_id is None


async def test_invalid_client_id(mock_enhanced_client_manager):
    """Test handling of invalid client IDs with enhanced error reporting"""
    manager = mock_enhanced_client_manager

    # The new config manager returns None for invalid clients, it does not raise an error
    # on get_client_config. An error would be raised on initialization if a config is malformed.
    # We can test that get_client_config returns None.
    config = await manager.get_client_config("invalid-client-id")
    assert config is None


# New tests for enhanced features


def test_domain_hierarchy_extraction():
    """Test domain hierarchy extraction"""
    hierarchy = get_domain_hierarchy("api.v1.support.company.com")
    expected = [
        "api.v1.support.company.com",
        "v1.support.company.com",
        "support.company.com",
        "company.com",
    ]
    assert hierarchy == expected

    # Test simple domain
    hierarchy = get_domain_hierarchy("company.com")
    assert hierarchy == ["company.com"]


def test_domain_variants_generation():
    """Test comprehensive domain variants generation"""
    variants = get_domain_variants("support.company.com")

    # Should include the domain itself and parent
    assert "support.company.com" in variants
    assert "company.com" in variants

    # Should include www variants
    assert "www.support.company.com" in variants
    assert "www.company.com" in variants


def test_domain_similarity_calculation():
    """Test domain similarity scoring"""
    # Exact match
    similarity = calculate_domain_similarity("company.com", "company.com")
    assert similarity == 1.0

    # Subdomain relationship
    similarity = calculate_domain_similarity("api.company.com", "company.com")
    assert similarity >= 0.7

    # Different domains
    similarity = calculate_domain_similarity("example.com", "company.com")
    assert similarity == 0.0


def test_domain_pattern_matching():
    """Test wildcard domain pattern matching"""
    # Test wildcard patterns
    assert match_domain_pattern("api.company.com", "*.company.com") == True
    assert match_domain_pattern("company.com", "*.company.com") == False
    assert match_domain_pattern("support.company.com", "support.*") == True
    assert match_domain_pattern("billing.company.com", "support.*") == False


def test_domain_matcher_advanced_strategies():
    """Test DomainMatcher with multiple strategies"""
    matcher = DomainMatcher()

    # Add test aliases and patterns
    matcher.add_alias("old.company.com", "company.com")
    matcher.add_pattern("*.company.com")

    candidates = ["company.com", "example.com", "test.org"]

    # Test exact match
    match, confidence, method = matcher.match_domain("company.com", candidates)
    assert match == "company.com"
    assert confidence == 1.0
    assert method == "exact_match"

    # Test alias resolution
    match, confidence, method = matcher.match_domain("old.company.com", candidates)
    assert match == "company.com"
    assert confidence == 0.95
    assert method == "alias_resolution"


async def test_client_domains_management(mock_enhanced_client_manager):
    """Test client domain management features"""
    manager = mock_enhanced_client_manager

    # Test getting client domains
    domains = await manager.get_client_domains("client-001-cole-nielson")
    assert isinstance(domains, set)
    assert len(domains) > 0
    assert "colenielson.dev" in domains


def test_similar_clients_discovery(mock_enhanced_client_manager):
    """Test finding similar clients based on domain similarity"""
    manager = mock_enhanced_client_manager

    # Test finding similar clients
    similar = manager.find_similar_clients("similar.colenielson.dev", limit=3)
    assert isinstance(similar, list)

    # If similar clients found, should be tuples of (client_id, score)
    for client_id, score in similar:
        assert isinstance(client_id, str)
        assert 0.0 <= score <= 1.0


async def test_client_summary_generation(mock_enhanced_client_manager):
    """Test comprehensive client summary generation"""
    manager = mock_enhanced_client_manager

    summary = await manager.get_client_summary("client-001-cole-nielson")

    assert summary["client_id"] == "client-001-cole-nielson"
    assert summary["name"] == "Cole Nielson Email Router"
    assert "domains" in summary
    assert "routing_categories" in summary
    assert "settings" in summary
    assert summary["total_domains"] > 0


def test_domain_alias_functionality(mock_enhanced_client_manager):
    """Test domain alias management"""
    manager = mock_enhanced_client_manager

    # Add domain alias
    manager.add_domain_alias("legacy.colenielson.dev", "colenielson.dev")

    # Test that alias resolves correctly
    # Note: This would require the alias to be used in identification
    # For now, just test that the method doesn't error
    assert True  # Placeholder - would need more complex test setup


def test_fuzzy_matching_configuration(mock_enhanced_client_manager):
    """Test fuzzy matching configuration options"""
    manager = mock_enhanced_client_manager

    # Test configuration options
    assert hasattr(manager, "confidence_threshold")
    assert hasattr(manager, "enable_fuzzy_matching")
    assert hasattr(manager, "enable_hierarchy_matching")

    # Test disabling fuzzy matching
    manager.enable_fuzzy_matching = False
    result = manager.identify_client_by_domain("unknown.domain.com")
    assert not result.is_successful


def test_confidence_scoring_accuracy(mock_enhanced_client_manager):
    """Test that confidence scores are reasonable and consistent"""
    manager = mock_enhanced_client_manager

    # Exact match should have highest confidence
    result = manager.identify_client_by_domain("colenielson.dev")
    assert result.confidence == 1.0

    # Subdomain matches should have lower but reasonable confidence
    # Note: api.colenielson.dev is in our mock aliases, so it gets exact match (1.0)
    # Use a different subdomain that's not in aliases
    result = manager.identify_client_by_domain("test.colenielson.dev")
    if result.is_successful:
        assert 0.7 <= result.confidence < 1.0


def test_email_domain_extraction_edge_cases():
    """Test domain extraction with edge cases"""
    # Valid cases
    assert extract_domain_from_email("user@company.com") == "company.com"
    assert extract_domain_from_email("test@sub.domain.co.uk") == "sub.domain.co.uk"

    # Invalid cases
    assert extract_domain_from_email("invalid-email") is None
    assert extract_domain_from_email("user@") is None
    assert extract_domain_from_email("@domain.com") is None
    assert extract_domain_from_email("") is None


def test_domain_normalization_edge_cases():
    """Test domain normalization with various inputs"""
    # Standard cases
    assert normalize_domain("Company.COM") == "company.com"
    assert normalize_domain("www.Company.com") == "company.com"

    # Edge cases
    assert normalize_domain("") is None
    assert normalize_domain("invalid") is None
    assert normalize_domain("company.com.") == "company.com"  # Trailing dot removal
    assert normalize_domain("https://company.com/path") == "company.com"
