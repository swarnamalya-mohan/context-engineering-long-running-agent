from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from repo_agent.llm import OpenAIResponsesLLM
from repo_agent.review_schema import ReviewAnalysis
from repo_agent.tools.github import GitHubTool, candidate_relevance


def test_discovery_does_not_stop_after_first_query():
    tool = GitHubTool()
    calls = []
    def get(url, **kwargs):
        calls.append(kwargs['params']['q'])
        if len(calls) == 1:
            items = [{'full_name': 'a/awesome-api-clients', 'description': 'API client list', 'stargazers_count': 99999}]
        else:
            items = [{'full_name': 'a/client', 'description': 'REST client for teams', 'stargazers_count': 20}]
        return SimpleNamespace(json=lambda: {'items': items})
    tool._get = get
    result = tool.search_alternatives('Postman', 1)
    assert len(calls) == 4
    assert result[0]['full_name'] == 'a/client'


def test_resource_list_never_ranks_above_product():
    assert candidate_relevance({'full_name': 'a/awesome-go', 'description': 'API client resources'}) == 0
    assert candidate_relevance({'full_name': 'a/client', 'description': 'API testing platform'}) > 0


def test_review_api_requests_schema_and_rejects_missing_output():
    llm = OpenAIResponsesLLM.__new__(OpenAIResponsesLLM)
    llm.model = 'test-model'
    arguments = []
    def parse(**kwargs):
        arguments.append(kwargs)
        return SimpleNamespace(output_parsed=None, status='incomplete')
    llm.client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    with pytest.raises(ValueError, match='structured analysis'):
        llm.review('instructions', 'source')
    assert arguments[0]['text_format'] is ReviewAnalysis


def test_review_schema_rejects_string_booleans():
    with pytest.raises(ValidationError):
        ReviewAnalysis.model_validate({'summary': 'x', 'self_hosted': 'true', 'rest_client': True,
            'team_collaboration': True, 'enterprise_sso': None, 'enterprise_sso_paid_only': None,
            'strengths': [], 'risks': [], 'evidence': [], 'confidence': .5})
