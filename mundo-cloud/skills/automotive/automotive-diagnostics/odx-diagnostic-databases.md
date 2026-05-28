# ODX - Open Diagnostic Data Exchange (ISO 22901)

## Overview

ODX (Open Diagnostic Data Exchange) is an XML-based standard for describing ECU diagnostic data. It enables tool-independent diagnostic implementations and provides complete ECU diagnostic metadata.

## ODX File Types

### ODX-D (Diagnostic Data)
- Diagnostic services
- Data identifiers (DIDs)
- Diagnostic trouble codes (DTCs)
- Routine definitions
- ECU variants

### ODX-C (Communication Parameters)
- CAN/LIN/FlexRay parameters
- Timing parameters
- Network topology

### ODX-V (Vehicle Data)
- ECU installation positions
- Vehicle variants
- ECU addressing

### ODX-F (Flash Data)
- Flash memory layout
- Flash programming sequences
- Bootloader parameters

## ODX Structure Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ODX MODEL-VERSION="2.2.0" xmlns="ISO22901">
  <DIAG-LAYER-CONTAINER ID="EngineECU">
    <BASE-VARIANT ID="EngineECU_BaseVariant">
      <SHORT-NAME>Engine ECU Diagnostics</SHORT-NAME>

      <!-- Diagnostic Services -->
      <DIAG-COMMS>
        <!-- Read Data By Identifier -->
        <DIAG-SERVICE ID="ReadDataByIdentifier" SEMANTIC="READ-DATA">
          <SHORT-NAME>ReadDataByIdentifier</SHORT-NAME>
          <REQUEST>
            <PARAM ID="Service" CODED-VALUE="0x22"/>
            <PARAM ID="DataIdentifier" xsi:type="VALUE"/>
          </REQUEST>
          <POS-RESPONSE>
            <PARAM ID="Service" CODED-VALUE="0x62"/>
            <PARAM ID="DataIdentifier" xsi:type="MATCHING-REQUEST-PARAM"/>
            <PARAM ID="Data" xsi:type="VALUE"/>
          </POS-RESPONSE>
        </DIAG-SERVICE>
      </DIAG-COMMS>

      <!-- Data Identifiers -->
      <DIAG-DATA-DICTIONARY-SPEC>
        <DATA-OBJECT-PROPS>
          <!-- VIN -->
          <DATA-OBJECT-PROP ID="VIN_0xF190">
            <SHORT-NAME>VehicleIdentificationNumber</SHORT-NAME>
            <LONG-NAME>VIN</LONG-NAME>
            <DIAG-CODED-TYPE BASE-DATA-TYPE="A_ASCII" xsi:type="STANDARD-LENGTH-TYPE">
              <BIT-LENGTH>136</BIT-LENGTH>  <!-- 17 bytes -->
            </DIAG-CODED-TYPE>
          </DATA-OBJECT-PROP>

          <!-- Engine Coolant Temperature -->
          <DATA-OBJECT-PROP ID="CoolantTemp_0x0105">
            <SHORT-NAME>EngineCoolantTemperature</SHORT-NAME>
            <COMPU-METHOD>
              <COMPU-INTERNAL-TO-PHYS>
                <COMPU-SCALES>
                  <COMPU-SCALE>
                    <LINEAR-COMPU-SCALE>
                      <COMPU-OFFSET>-40</COMPU-OFFSET>
                      <COMPU-SCALE>1</COMPU-SCALE>
                    </LINEAR-COMPU-SCALE>
                  </COMPU-SCALE>
                </COMPU-SCALES>
              </COMPU-INTERNAL-TO-PHYS>
            </COMPU-METHOD>
            <UNIT-REF ID-REF="Celsius"/>
          </DATA-OBJECT-PROP>
        </DATA-OBJECT-PROPS>
      </DIAG-DATA-DICTIONARY-SPEC>

      <!-- DTCs -->
      <DIAG-TROUBLE-CODE-PROPS>
        <DTC ID="DTC_P0171">
          <SHORT-NAME>SystemTooLeanBank1</SHORT-NAME>
          <TROUBLE-CODE>0x0171</TROUBLE-CODE>
          <TEXT>System Too Lean (Bank 1)</TEXT>
          <DISPLAY-TROUBLE-CODE>P0171</DISPLAY-TROUBLE-CODE>
          <LEVEL>2</LEVEL>  <!-- Severity -->
        </DTC>
      </DIAG-TROUBLE-CODE-PROPS>
    </BASE-VARIANT>
  </DIAG-LAYER-CONTAINER>
</ODX>
```

## Production Code - ODX Parser

```python
#!/usr/bin/env python3
"""
ODX Parser using odxtools library
Supports ODX-D 2.2.0 format
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class ODXDataIdentifier:
    """ODX Data Identifier definition."""
    did: int
    short_name: str
    long_name: str
    bit_length: int
    data_type: str
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None

@dataclass
class ODXDTC:
    """ODX DTC definition."""
    code: str  # Display code (e.g., "P0171")
    trouble_code: int  # Numeric code
    short_name: str
    description: str
    severity: int = 2

class ODXParser:
    """Parse ODX diagnostic database files."""

    ODX_NAMESPACE = {'odx': 'ISO22901'}

    def __init__(self, odx_file: str):
        """
        Initialize ODX parser.

        Args:
            odx_file: Path to ODX XML file
        """
        self.odx_file = odx_file
        self.tree = ET.parse(odx_file)
        self.root = self.tree.getroot()
        self.dids: Dict[int, ODXDataIdentifier] = {}
        self.dtcs: Dict[str, ODXDTC] = {}
        self.services: Dict[str, Dict] = {}

        self._parse()

    def _parse(self):
        """Parse ODX file."""
        self._parse_data_identifiers()
        self._parse_dtcs()
        self._parse_services()

    def _parse_data_identifiers(self):
        """Parse data identifiers from ODX."""
        # Find all DATA-OBJECT-PROP elements
        for prop in self.root.findall('.//DATA-OBJECT-PROP', self.ODX_NAMESPACE):
            try:
                # Extract DID from ID attribute (e.g., "VIN_0xF190")
                prop_id = prop.get('ID', '')
                if '_0x' not in prop_id:
                    continue

                did_str = prop_id.split('_0x')[1]
                did = int(did_str, 16)

                # Extract metadata
                short_name_elem = prop.find('SHORT-NAME', self.ODX_NAMESPACE)
                long_name_elem = prop.find('LONG-NAME', self.ODX_NAMESPACE)

                short_name = short_name_elem.text if short_name_elem is not None else ''
                long_name = long_name_elem.text if long_name_elem is not None else ''

                # Extract data type and length
                coded_type = prop.find('.//DIAG-CODED-TYPE', self.ODX_NAMESPACE)
                bit_length = 0
                data_type = 'UNKNOWN'

                if coded_type is not None:
                    data_type = coded_type.get('BASE-DATA-TYPE', 'UNKNOWN')
                    bit_length_elem = coded_type.find('BIT-LENGTH', self.ODX_NAMESPACE)
                    if bit_length_elem is not None:
                        bit_length = int(bit_length_elem.text)

                # Extract computation method (scaling)
                scale = 1.0
                offset = 0.0
                unit = ''

                compu_method = prop.find('.//COMPU-METHOD', self.ODX_NAMESPACE)
                if compu_method is not None:
                    linear_scale = compu_method.find('.//LINEAR-COMPU-SCALE', self.ODX_NAMESPACE)
                    if linear_scale is not None:
                        scale_elem = linear_scale.find('COMPU-SCALE', self.ODX_NAMESPACE)
                        offset_elem = linear_scale.find('COMPU-OFFSET', self.ODX_NAMESPACE)

                        if scale_elem is not None:
                            scale = float(scale_elem.text)
                        if offset_elem is not None:
                            offset = float(offset_elem.text)

                # Extract unit
                unit_ref = prop.find('.//UNIT-REF', self.ODX_NAMESPACE)
                if unit_ref is not None:
                    unit = unit_ref.get('ID-REF', '')

                # Create DID object
                did_obj = ODXDataIdentifier(
                    did=did,
                    short_name=short_name,
                    long_name=long_name,
                    bit_length=bit_length,
                    data_type=data_type,
                    scale=scale,
                    offset=offset,
                    unit=unit
                )

                self.dids[did] = did_obj

            except Exception as e:
                print(f"Error parsing DID: {e}")

    def _parse_dtcs(self):
        """Parse DTCs from ODX."""
        for dtc_elem in self.root.findall('.//DTC', self.ODX_NAMESPACE):
            try:
                # Extract DTC information
                short_name_elem = dtc_elem.find('SHORT-NAME', self.ODX_NAMESPACE)
                text_elem = dtc_elem.find('TEXT', self.ODX_NAMESPACE)
                code_elem = dtc_elem.find('TROUBLE-CODE', self.ODX_NAMESPACE)
                display_code_elem = dtc_elem.find('DISPLAY-TROUBLE-CODE', self.ODX_NAMESPACE)
                level_elem = dtc_elem.find('LEVEL', self.ODX_NAMESPACE)

                if display_code_elem is None or code_elem is None:
                    continue

                display_code = display_code_elem.text
                trouble_code = int(code_elem.text, 16)
                short_name = short_name_elem.text if short_name_elem is not None else ''
                description = text_elem.text if text_elem is not None else ''
                severity = int(level_elem.text) if level_elem is not None else 2

                dtc = ODXDTC(
                    code=display_code,
                    trouble_code=trouble_code,
                    short_name=short_name,
                    description=description,
                    severity=severity
                )

                self.dtcs[display_code] = dtc

            except Exception as e:
                print(f"Error parsing DTC: {e}")

    def _parse_services(self):
        """Parse diagnostic services from ODX."""
        for service_elem in self.root.findall('.//DIAG-SERVICE', self.ODX_NAMESPACE):
            try:
                short_name_elem = service_elem.find('SHORT-NAME', self.ODX_NAMESPACE)
                if short_name_elem is None:
                    continue

                service_name = short_name_elem.text
                semantic = service_elem.get('SEMANTIC', '')

                # Parse request parameters
                request_elem = service_elem.find('REQUEST', self.ODX_NAMESPACE)
                request_params = []

                if request_elem is not None:
                    for param in request_elem.findall('PARAM', self.ODX_NAMESPACE):
                        param_info = {
                            'id': param.get('ID', ''),
                            'coded_value': param.get('CODED-VALUE', ''),
                        }
                        request_params.append(param_info)

                self.services[service_name] = {
                    'semantic': semantic,
                    'request_params': request_params,
                }

            except Exception as e:
                print(f"Error parsing service: {e}")

    def get_did_info(self, did: int) -> Optional[ODXDataIdentifier]:
        """Get DID information by identifier."""
        return self.dids.get(did)

    def get_dtc_info(self, dtc_code: str) -> Optional[ODXDTC]:
        """Get DTC information by code."""
        return self.dtcs.get(dtc_code)

    def export_to_json(self, output_file: str):
        """Export parsed ODX data to JSON."""
        data = {
            'dids': {f"0x{did:04X}": {
                'name': info.short_name,
                'long_name': info.long_name,
                'length': info.bit_length // 8,
                'type': info.data_type,
                'scale': info.scale,
                'offset': info.offset,
                'unit': info.unit,
            } for did, info in self.dids.items()},
            'dtcs': {code: {
                'name': dtc.short_name,
                'description': dtc.description,
                'severity': dtc.severity,
            } for code, dtc in self.dtcs.items()},
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

# Example usage
if __name__ == "__main__":
    # Parse ODX file
    parser = ODXParser("engine_ecu.odx")

    print(f"Parsed {len(parser.dids)} DIDs")
    print(f"Parsed {len(parser.dtcs)} DTCs")

    # Get specific DID info
    vin_info = parser.get_did_info(0xF190)
    if vin_info:
        print(f"\nVIN DID:")
        print(f"  Name: {vin_info.short_name}")
        print(f"  Length: {vin_info.bit_length // 8} bytes")

    # Get specific DTC info
    dtc_info = parser.get_dtc_info("P0171")
    if dtc_info:
        print(f"\nDTC P0171:")
        print(f"  Description: {dtc_info.description}")
        print(f"  Severity: {dtc_info.severity}")

    # Export to JSON
    parser.export_to_json("diagnostic_database.json")
    print("\nExported to JSON")
```

## Creating ODX Files

### Basic ODX Template

```python
#!/usr/bin/env python3
"""
ODX File Generator
Creates ODX diagnostic database from Python definitions
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_odx_template(ecu_name: str, output_file: str):
    """Create basic ODX template."""
    # Create root element
    odx = ET.Element('ODX')
    odx.set('MODEL-VERSION', '2.2.0')
    odx.set('xmlns', 'ISO22901')

    # Create DIAG-LAYER-CONTAINER
    container = ET.SubElement(odx, 'DIAG-LAYER-CONTAINER')
    container.set('ID', f"{ecu_name}_Container")

    # Create BASE-VARIANT
    variant = ET.SubElement(container, 'BASE-VARIANT')
    variant.set('ID', f"{ecu_name}_BaseVariant")

    short_name = ET.SubElement(variant, 'SHORT-NAME')
    short_name.text = f"{ecu_name} Diagnostics"

    # Add DIAG-COMMS section
    diag_comms = ET.SubElement(variant, 'DIAG-COMMS')

    # Add DIAG-DATA-DICTIONARY-SPEC section
    data_dict = ET.SubElement(variant, 'DIAG-DATA-DICTIONARY-SPEC')
    data_props = ET.SubElement(data_dict, 'DATA-OBJECT-PROPS')

    # Add DIAG-TROUBLE-CODE-PROPS section
    dtc_props = ET.SubElement(variant, 'DIAG-TROUBLE-CODE-PROPS')

    # Pretty print and save
    xml_str = minidom.parseString(ET.tostring(odx)).toprettyxml(indent="  ")
    with open(output_file, 'w') as f:
        f.write(xml_str)

    print(f"Created ODX template: {output_file}")

# Example: Create template
if __name__ == "__main__":
    create_odx_template("EngineECU", "engine_ecu_template.odx")
```

## Best Practices

1. **Use ODX for all diagnostic metadata** - eliminates hardcoded values
2. **Version control ODX files** - track ECU software changes
3. **Validate ODX files** against ISO 22901 schema
4. **Export to JSON** for runtime performance
5. **Include comprehensive DTC descriptions** with repair procedures
6. **Document scaling formulas** in ODX for physical values
7. **Use ODX-C for communication parameters** - avoid hardcoded CAN IDs

## References

- ISO 22901-1 - ODX general information and use cases
- ISO 22901-2 - ODX data model
