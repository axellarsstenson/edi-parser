import json
from datetime import datetime
from typing import Dict, List, Optional

class EDIParser:
    def __init__(self):
        self.segments = []
        self.current_claim = {}
        self.claims = []
        
    def parse_string(self, content: str) -> List[Dict]:
        """Parse an EDI string and return a list of claims in JSON format."""
        # Clean the input data
        content = content.strip()
        if not content:
            return []
        # Split into segments
        self.segments = [seg for seg in content.split('~') if seg.strip()]
        
        # Process segments
        i = 0
        while i < len(self.segments):
            segment = self.segments[i]
            segment_type = segment.split('*')[0]
            
            if segment_type == 'CLM':
                if self.current_claim:
                    self.claims.append(self.current_claim.copy())
                self.current_claim = {}
                self._parse_claim(segment)
            elif segment_type == 'NM1':
                self._parse_name(segment)
            elif segment_type == 'N3':
                self._parse_address_line(segment)
            elif segment_type == 'N4':
                self._parse_address_city(segment)
            elif segment_type == 'DMG':
                self._parse_demographics(segment)
            elif segment_type == 'HI':
                self._parse_diagnosis(segment)
            elif segment_type == 'SV1':
                self._parse_service(segment)
            elif segment_type == 'DTP':
                self._parse_dates(segment)
            
            i += 1
            
        # Add the last claim
        if self.current_claim:
            self.claims.append(self.current_claim.copy())
            
        return self.claims
    
    def _parse_claim(self, segment: str):
        """Parse CLM (claim) segment."""
        parts = segment.split('*')
        if len(parts) < 4:
            return
            
        try:
            self.current_claim['claim_number'] = parts[1] if parts[1] != '' else None
            self.current_claim['amount'] = float(parts[2]) if parts[2] != '' else None
            self.current_claim['claim_type'] = parts[3] if parts[3] != '' else None
        except (ValueError, IndexError):
            pass
        
    def _parse_name(self, segment: str):
        """Parse NM1 (name) segment."""
        parts = segment.split('*')
        if len(parts) < 2:
            return
            
        entity_type = parts[1]
        
        name_info = {
            'last_name': parts[3] if len(parts) > 3 else None,
            'first_name': parts[4] if len(parts) > 4 else None,
            'middle_name': parts[5] if len(parts) > 5 and parts[5] != '' else None,
            'id_number': parts[9] if len(parts) > 9 and parts[9] != '' else None
        }
        
        if entity_type == 'IL':  # Insured
            self.current_claim['insured'] = name_info
        elif entity_type == 'QC':  # Patient
            self.current_claim['patient'] = name_info
        elif entity_type == '82':  # Rendering Provider
            self.current_claim['rendering_provider'] = name_info
        elif entity_type == 'DN':  # Referring Provider
            self.current_claim['referring_provider'] = name_info
        elif entity_type == '77':  # Service Facility
            self.current_claim['service_facility'] = {
                'name': parts[3],
                'id': parts[9] if len(parts) > 9 else None
            }
            
    def _parse_address_line(self, segment: str):
        """Parse N3 (address) segment."""
        parts = segment.split('*')
        if len(parts) < 2:
            return
            
        address = {
            'address_line_1': parts[1] if parts[1] != '' else None,
            'address_line_2': parts[2] if len(parts) > 2 and parts[2] != '' else None
        }
        
        if 'service_facility' in self.current_claim:
            self.current_claim['service_facility']['address'] = address
        else:
            if 'address' not in self.current_claim:
                self.current_claim['address'] = {}
            self.current_claim['address'].update(address)
            
    def _parse_address_city(self, segment: str):
        """Parse N4 (city/state/zip) segment."""
        parts = segment.split('*')
        address = {
            'city': parts[1],
            'state': parts[2],
            'zip': parts[3]
        }
        
        if 'service_facility' in self.current_claim:
            if 'address' not in self.current_claim['service_facility']:
                self.current_claim['service_facility']['address'] = {}
            self.current_claim['service_facility']['address'].update(address)
        else:
            if 'address' not in self.current_claim:
                self.current_claim['address'] = {}
            self.current_claim['address'].update(address)
            
    def _parse_demographics(self, segment: str):
        """Parse DMG (demographics) segment."""
        parts = segment.split('*')
        if len(parts) > 2 and parts[2]:
            try:
                dob = datetime.strptime(parts[2], '%Y%m%d').strftime('%Y-%m-%d')
            except ValueError:
                dob = parts[2]
        else:
            dob = None
            
        demographics = {
            'date_of_birth': dob,
            'gender': parts[3] if len(parts) > 3 else None
        }
        
        self.current_claim['demographics'] = demographics
        
    def _parse_diagnosis(self, segment: str):
        """Parse HI (diagnosis) segment."""
        parts = segment.split('*')
        diagnoses = []
        
        for part in parts[1:]:
            if part:
                code_parts = part.split(':')
                if len(code_parts) > 1:
                    diagnoses.append(code_parts[1])
                    
        if diagnoses:
            self.current_claim['diagnoses'] = diagnoses
            
    def _parse_service(self, segment: str):
        """Parse SV1 (service) segment."""
        parts = segment.split('*')
        
        service = {
            'procedure_code': parts[1].split(':')[1] if ':' in parts[1] else parts[1],
            'amount': float(parts[2]) if parts[2] else None,
            'units': parts[4] if len(parts) > 4 else None
        }
        
        if 'services' not in self.current_claim:
            self.current_claim['services'] = []
        self.current_claim['services'].append(service)
        
    def _parse_dates(self, segment: str):
        """Parse DTP (dates) segment."""
        parts = segment.split('*')
        if len(parts) > 2 and parts[1] == '472':  # Service Date
            try:
                service_date = datetime.strptime(parts[3], '%Y%m%d').strftime('%Y-%m-%d')
            except ValueError:
                service_date = parts[3]
            self.current_claim['service_date'] = service_date

def parse_edi_to_json(input_data: str, output_file: str = None):
    """
    Parse EDI data and optionally save the results as JSON.
    
    Args:
        input_data (str): EDI content as a string
        output_file (str, optional): Path where the JSON output should be saved.
            If None, returns the parsed data as a dictionary.
    
    Returns:
        dict: If output_file is None, returns the parsed claims data
    """
    parser = EDIParser()
    claims = parser.parse_string(input_data)
    result = {'claims': claims}
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        return result

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python edi_parser.py <input_file> <output_file>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        input_data = f.read()
    
    parse_edi_to_json(input_data, sys.argv[2])