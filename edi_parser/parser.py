import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EDIParser:
    def __init__(self):
        self.segments = []
        self.current_claim = {}
        self.claims = []
        
    def parse_string(self, content: str) -> List[Dict]:
        """
        Parse an EDI string and return a list of claims in JSON format.
        
        Args:
            content (str): The EDI content to parse
            
        Returns:
            List[Dict]: List of parsed claims
            
        Raises:
            TypeError: If input is not a string
        """
        if not isinstance(content, str):
            raise TypeError("Input must be a string")
            
        # Clean the input data
        content = content.strip()
        if not content:
            return []
            
        # Split into segments and filter empty ones
        self.segments = [seg.strip() for seg in content.split('~') if seg.strip()]
        
        # Process segments
        i = 0
        while i < len(self.segments):
            try:
                segment = self.segments[i]
                parts = segment.split('*')
                if not parts:
                    i += 1
                    continue
                    
                segment_type = parts[0]
                
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
                
            except Exception as e:
                logger.warning(f"Error processing segment {i}: {str(e)}")
                
            i += 1
            
        # Add the last claim
        if self.current_claim:
            self.claims.append(self.current_claim.copy())
            
        return self.claims
    
    def _safe_split(self, segment: str) -> List[str]:
        """Safely split a segment into parts."""
        try:
            return segment.split('*')
        except Exception:
            return []
    
    def _parse_claim(self, segment: str) -> None:
        """Parse CLM (claim) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 4:
            logger.warning(f"Invalid claim segment: {segment}")
            return
            
        try:
            self.current_claim['claim_number'] = parts[1].strip() if parts[1].strip() else None
            self.current_claim['amount'] = float(parts[2]) if parts[2].strip() else None
            self.current_claim['claim_type'] = parts[3].strip() if parts[3].strip() else None
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing claim values: {str(e)}")
    
    def _parse_name(self, segment: str) -> None:
        """Parse NM1 (name) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 2:
            return
            
        entity_type = parts[1].strip()
        
        try:
            name_info = {
                'last_name': parts[3].strip() if len(parts) > 3 and parts[3].strip() else None,
                'first_name': parts[4].strip() if len(parts) > 4 and parts[4].strip() else None,
                'middle_name': parts[5].strip() if len(parts) > 5 and parts[5].strip() else None,
                'id_number': parts[9].strip() if len(parts) > 9 and parts[9].strip() else None
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
                    'name': parts[3].strip() if len(parts) > 3 else None,
                    'id': parts[9].strip() if len(parts) > 9 else None
                }
        except Exception as e:
            logger.warning(f"Error parsing name segment: {str(e)}")
    
    def _parse_address_line(self, segment: str) -> None:
        """Parse N3 (address) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 2:
            return
            
        try:
            address = {
                'address_line_1': parts[1].strip() if parts[1].strip() else None,
                'address_line_2': parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
            }
            
            if 'service_facility' in self.current_claim:
                self.current_claim['service_facility']['address'] = address
            else:
                if 'address' not in self.current_claim:
                    self.current_claim['address'] = {}
                self.current_claim['address'].update(address)
        except Exception as e:
            logger.warning(f"Error parsing address line: {str(e)}")
    
    def _parse_address_city(self, segment: str) -> None:
        """Parse N4 (city/state/zip) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 4:
            return
            
        try:
            address = {
                'city': parts[1].strip() if parts[1].strip() else None,
                'state': parts[2].strip() if parts[2].strip() else None,
                'zip': parts[3].strip() if parts[3].strip() else None
            }
            
            if 'service_facility' in self.current_claim:
                if 'address' not in self.current_claim['service_facility']:
                    self.current_claim['service_facility']['address'] = {}
                self.current_claim['service_facility']['address'].update(address)
            else:
                if 'address' not in self.current_claim:
                    self.current_claim['address'] = {}
                self.current_claim['address'].update(address)
        except Exception as e:
            logger.warning(f"Error parsing city/state/zip: {str(e)}")
    
    def _parse_demographics(self, segment: str) -> None:
        """Parse DMG (demographics) segment."""
        parts = self._safe_split(segment)
        try:
            if len(parts) > 2 and parts[2].strip():
                try:
                    dob = datetime.strptime(parts[2], '%Y%m%d').strftime('%Y-%m-%d')
                except ValueError:
                    dob = parts[2]
            else:
                dob = None
                
            demographics = {
                'date_of_birth': dob,
                'gender': parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
            }
            
            self.current_claim['demographics'] = demographics
        except Exception as e:
            logger.warning(f"Error parsing demographics: {str(e)}")
    
    def _parse_diagnosis(self, segment: str) -> None:
        """Parse HI (diagnosis) segment."""
        parts = self._safe_split(segment)
        diagnoses = []
        
        try:
            for part in parts[1:]:
                if part.strip():
                    code_parts = part.split(':')
                    if len(code_parts) > 1:
                        diagnoses.append(code_parts[1].strip())
                        
            if diagnoses:
                self.current_claim['diagnoses'] = diagnoses
        except Exception as e:
            logger.warning(f"Error parsing diagnosis codes: {str(e)}")
    
    def _parse_service(self, segment: str) -> None:
        """Parse SV1 (service) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 3:
            return
            
        try:
            service = {
                'procedure_code': parts[1].split(':')[1].strip() if ':' in parts[1] else parts[1].strip(),
                'amount': float(parts[2]) if parts[2].strip() else None,
                'units': parts[4].strip() if len(parts) > 4 and parts[4].strip() else None
            }
            
            if 'services' not in self.current_claim:
                self.current_claim['services'] = []
            self.current_claim['services'].append(service)
        except Exception as e:
            logger.warning(f"Error parsing service: {str(e)}")
    
    def _parse_dates(self, segment: str) -> None:
        """Parse DTP (dates) segment."""
        parts = self._safe_split(segment)
        if len(parts) < 4:
            return
            
        try:
            if parts[1] == '472':  # Service Date
                try:
                    service_date = datetime.strptime(parts[3], '%Y%m%d').strftime('%Y-%m-%d')
                except ValueError:
                    service_date = parts[3]
                self.current_claim['service_date'] = service_date
        except Exception as e:
            logger.warning(f"Error parsing dates: {str(e)}")

def parse_edi_to_json(input_data: str, output_file: Optional[str] = None) -> Optional[Dict]:
    """
    Parse EDI data and optionally save the results as JSON.
    
    Args:
        input_data (str): EDI content as a string
        output_file (str, optional): Path where the JSON output should be saved.
            If None, returns the parsed data as a dictionary.
    
    Returns:
        dict: If output_file is None, returns the parsed claims data
        
    Raises:
        TypeError: If input_data is not a string
    """
    parser = EDIParser()
    claims = parser.parse_string(input_data)
    result = {'claims': claims}
    
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Successfully wrote JSON to {output_file}")
        except Exception as e:
            logger.error(f"Error writing to output file: {str(e)}")
            raise
    else:
        return result

def main():
    parser = argparse.ArgumentParser(description='Parse EDI claims files to JSON')
    parser.add_argument('input_file', help='Input EDI file to parse')
    parser.add_argument('-o', '--output', help='Output JSON file (if not specified, prints to stdout)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_data = f.read()
        
        result = parse_edi_to_json(input_data, args.output)
        if not args.output:
            print(json.dumps(result, indent=2))
            
    except UnicodeDecodeError:
        logger.error(f"Could not decode {args.input_file}. Please ensure it's a valid text file.")
        return 1
    except FileNotFoundError:
        logger.error(f"Could not find input file {args.input_file}")
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())