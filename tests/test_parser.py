import pytest
from edi_parser.parser import EDIParser

@pytest.fixture
def parser():
    return EDIParser()

def test_parse_simple_claim():
    parser = EDIParser()
    sample_edi = "CLM*12345*100*24:B:1*Y*A*Y*Y~NM1*IL*1*DOE*JOHN****MI*12345"
    result = parser.parse_string(sample_edi)
    
    assert len(result) == 1
    assert result[0]['claim_number'] == '12345'
    assert result[0]['amount'] == 100.0

def test_parse_empty_input():
    parser = EDIParser()
    result = parser.parse_string("")
    assert len(result) == 0

def test_parse_invalid_input():
    parser = EDIParser()
    result = parser.parse_string("INVALID*DATA")
    assert len(result) == 0