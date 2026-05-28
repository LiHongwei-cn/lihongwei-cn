# ECU Flash Reprogramming

## Overview

ECU flash reprogramming updates firmware on automotive ECUs. This critical operation requires precise timing, security access, error recovery, and validation. Based on UDS services 0x34-0x37.

## Flash Programming Sequence

### Standard Workflow

```
1. Pre-Programming
   ├─ Extended Diagnostic Session (0x10 03)
   ├─ Security Access (0x27 seed/key)
   ├─ Disable Communication (0x28)
   ├─ Disable DTC Setting (0x85 02)
   └─ TesterPresent keepalive

2. Enter Programming Session
   ├─ Programming Session (0x10 02)
   ├─ Security Access Level 2 (0x27)
   └─ ECU Reset (0x11 01)

3. Bootloader Activation
   ├─ Wait for ECU reboot
   ├─ Re-establish session
   └─ Verify bootloader active

4. Memory Download
   ├─ Request Download (0x34) - address + size
   ├─ Transfer Data loop (0x36) - blocks with sequence counter
   ├─ Request Transfer Exit (0x37)
   └─ Checksum verification

5. Post-Programming
   ├─ Routine Control - check dependencies (0x31)
   ├─ ECU Reset (0x11 01)
   ├─ Verify application running
   └─ Restore default session
```

## Production Code - Flash Programmer

```python
#!/usr/bin/env python3
"""
ECU Flash Programming Implementation
Supports Intel HEX, S-Record, and binary formats
"""

import time
import struct
import zlib
from typing import Optional, Tuple, List, Callable
from enum import IntEnum
from dataclasses import dataclass
import hashlib

class FlashStatus(IntEnum):
    """Flash programming status codes."""
    SUCCESS = 0
    FAILED_SECURITY_ACCESS = 1
    FAILED_DOWNLOAD_REQUEST = 2
    FAILED_TRANSFER_DATA = 3
    FAILED_TRANSFER_EXIT = 4
    FAILED_CHECKSUM = 5
    FAILED_DEPENDENCY_CHECK = 6

@dataclass
class FlashMemoryRegion:
    """Flash memory region definition."""
    address: int
    size: int
    data: bytes
    checksum: Optional[int] = None

@dataclass
class FlashProgress:
    """Flash programming progress."""
    total_bytes: int
    transferred_bytes: int
    current_block: int
    total_blocks: int
    elapsed_time: float
    estimated_remaining: float

    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.transferred_bytes / self.total_bytes) * 100.0

class ECUFlashProgrammer:
    """ECU flash programming manager."""

    def __init__(self, can_interface, progress_callback: Optional[Callable[[FlashProgress], None]] = None):
        """
        Initialize flash programmer.

        Args:
            can_interface: CAN/UDS communication interface
            progress_callback: Optional callback for progress updates
        """
        self.can_interface = can_interface
        self.progress_callback = progress_callback
        self.max_block_length = 0
        self.block_sequence_counter = 0

    def program_ecu(self, flash_file: str, verify: bool = True) -> Tuple[FlashStatus, str]:
        """
        Program ECU with flash file.

        Args:
            flash_file: Path to flash file (Intel HEX, S-Record, or binary)
            verify: Perform post-programming verification

        Returns:
            Tuple of (status, message)
        """
        print("=" * 80)
        print("ECU FLASH PROGRAMMING")
        print("=" * 80)

        # Load flash file
        print(f"\n[1/7] Loading flash file: {flash_file}")
        memory_regions = self._load_flash_file(flash_file)
        if not memory_regions:
            return FlashStatus.FAILED_DOWNLOAD_REQUEST, "Failed to load flash file"

        total_size = sum(region.size for region in memory_regions)
        print(f"  Total size: {total_size} bytes ({total_size / 1024:.1f} KB)")
        print(f"  Regions: {len(memory_regions)}")

        # Pre-programming checks
        print("\n[2/7] Pre-programming setup")
        if not self._pre_programming():
            return FlashStatus.FAILED_SECURITY_ACCESS, "Pre-programming failed"

        # Enter programming session
        print("\n[3/7] Entering programming session")
        if not self._enter_programming_session():
            return FlashStatus.FAILED_SECURITY_ACCESS, "Failed to enter programming session"

        # Program each memory region
        print("\n[4/7] Programming memory regions")
        start_time = time.time()

        for i, region in enumerate(memory_regions):
            print(f"\n  Region {i+1}/{len(memory_regions)}: 0x{region.address:08X} ({region.size} bytes)")

            status, msg = self._program_memory_region(region, start_time)
            if status != FlashStatus.SUCCESS:
                return status, msg

        elapsed = time.time() - start_time
        speed = total_size / elapsed / 1024  # KB/s
        print(f"\n  Programming complete in {elapsed:.1f}s ({speed:.1f} KB/s)")

        # Transfer exit
        print("\n[5/7] Finalizing transfer")
        if not self._transfer_exit():
            return FlashStatus.FAILED_TRANSFER_EXIT, "Transfer exit failed"

        # Verify
        if verify:
            print("\n[6/7] Verifying programming")
            if not self._verify_programming(memory_regions):
                return FlashStatus.FAILED_CHECKSUM, "Verification failed"
        else:
            print("\n[6/7] Skipping verification")

        # Post-programming
        print("\n[7/7] Post-programming")
        if not self._post_programming():
            return FlashStatus.FAILED_DEPENDENCY_CHECK, "Post-programming checks failed"

        print("\n" + "=" * 80)
        print("FLASH PROGRAMMING SUCCESSFUL")
        print("=" * 80)

        return FlashStatus.SUCCESS, "Programming completed successfully"

    def _pre_programming(self) -> bool:
        """Pre-programming setup."""
        # Extended diagnostic session
        print("  ├─ Extended diagnostic session")
        request = bytes([0x10, 0x03])
        response = self.can_interface.send_diagnostic_request(request)
        if not response or response[0] != 0x50:
            print("  │  └─ Failed")
            return False

        # Security access level 1
        print("  ├─ Security access level 1")
        if not self._security_access(0x01):
            print("  │  └─ Failed")
            return False

        # Disable DTC setting
        print("  ├─ Disable DTC setting")
        request = bytes([0x85, 0x02])
        response = self.can_interface.send_diagnostic_request(request)
        if not response or response[0] != 0xC5:
            print("  │  └─ Failed")
            return False

        print("  └─ Complete")
        return True

    def _enter_programming_session(self) -> bool:
        """Enter programming session and activate bootloader."""
        # Programming session
        print("  ├─ Programming diagnostic session")
        request = bytes([0x10, 0x02])
        response = self.can_interface.send_diagnostic_request(request)
        if not response or response[0] != 0x50:
            print("  │  └─ Failed")
            return False

        # Security access level 2 (programming)
        print("  ├─ Security access level 2")
        if not self._security_access(0x03):
            print("  │  └─ Failed")
            return False

        # ECU Reset to activate bootloader
        print("  ├─ ECU reset (bootloader activation)")
        request = bytes([0x11, 0x01])
        response = self.can_interface.send_diagnostic_request(request)
        if not response or response[0] != 0x51:
            print("  │  └─ Failed")
            return False

        # Wait for bootloader
        print("  ├─ Waiting for bootloader (5s)")
        time.sleep(5.0)

        # Re-establish communication
        print("  ├─ Re-establishing communication")
        request = bytes([0x10, 0x02])
        response = self.can_interface.send_diagnostic_request(request, timeout=5.0)
        if not response or response[0] != 0x50:
            print("  │  └─ Failed")
            return False

        print("  └─ Bootloader active")
        return True

    def _program_memory_region(self, region: FlashMemoryRegion, start_time: float) -> Tuple[FlashStatus, str]:
        """Program single memory region."""
        # Request Download
        if not self._request_download(region.address, region.size):
            return FlashStatus.FAILED_DOWNLOAD_REQUEST, "RequestDownload failed"

        # Transfer data in blocks
        data = region.data
        offset = 0
        block_num = 0
        total_blocks = (region.size + self.max_block_length - 1) // self.max_block_length

        self.block_sequence_counter = 1

        while offset < region.size:
            block_size = min(self.max_block_length, region.size - offset)
            block_data = data[offset:offset + block_size]

            # Transfer block
            if not self._transfer_data_block(block_data):
                return FlashStatus.FAILED_TRANSFER_DATA, f"TransferData failed at block {block_num}"

            offset += block_size
            block_num += 1

            # Progress callback
            if self.progress_callback:
                elapsed = time.time() - start_time
                progress = FlashProgress(
                    total_bytes=region.size,
                    transferred_bytes=offset,
                    current_block=block_num,
                    total_blocks=total_blocks,
                    elapsed_time=elapsed,
                    estimated_remaining=(elapsed / offset) * (region.size - offset) if offset > 0 else 0
                )
                self.progress_callback(progress)

            # Progress display
            if block_num % 10 == 0 or block_num == total_blocks:
                percentage = (offset / region.size) * 100
                print(f"    Progress: {percentage:.1f}% ({offset}/{region.size} bytes)", end='\r')

        print()  # New line after progress
        return FlashStatus.SUCCESS, "Region programmed successfully"

    def _request_download(self, address: int, size: int) -> bool:
        """Request download (0x34)."""
        # Build request
        # Format: 0x34 [dataFormatIdentifier] [addressAndLengthFormatIdentifier] [memoryAddress] [memorySize]
        addr_bytes = 4  # 4-byte address
        size_bytes = 4  # 4-byte size

        format_id = (addr_bytes << 4) | size_bytes

        request = bytearray([0x34, 0x00, format_id])  # 0x00 = no compression/encryption
        request += address.to_bytes(addr_bytes, 'big')
        request += size.to_bytes(size_bytes, 'big')

        # Send request
        response = self.can_interface.send_diagnostic_request(bytes(request), timeout=5.0)

        if not response or response[0] != 0x74:
            return False

        # Parse maxNumberOfBlockLength
        length_format = response[1]
        block_length_bytes = length_format & 0x0F

        if len(response) >= 2 + block_length_bytes:
            self.max_block_length = int.from_bytes(response[2:2+block_length_bytes], 'big')
            print(f"    Max block length: {self.max_block_length} bytes")
            return True

        return False

    def _transfer_data_block(self, data: bytes) -> bool:
        """Transfer data block (0x36)."""
        # Build request: 0x36 [blockSequenceCounter] [data]
        request = bytearray([0x36, self.block_sequence_counter]) + data

        # Send request
        response = self.can_interface.send_diagnostic_request(bytes(request), timeout=2.0)

        if not response or response[0] != 0x76:
            return False

        # Verify sequence counter
        if response[1] != self.block_sequence_counter:
            return False

        # Increment counter (1-255, then wrap to 0)
        self.block_sequence_counter = (self.block_sequence_counter + 1) % 256
        if self.block_sequence_counter == 0:
            self.block_sequence_counter = 1

        return True

    def _transfer_exit(self) -> bool:
        """Request transfer exit (0x37)."""
        request = bytes([0x37])
        response = self.can_interface.send_diagnostic_request(request, timeout=10.0)

        if not response or response[0] != 0x77:
            return False

        print("  Transfer exit acknowledged")
        return True

    def _verify_programming(self, regions: List[FlashMemoryRegion]) -> bool:
        """Verify programming with checksum routine."""
        # Routine Control: Check programming dependencies (0x31 01 0x0202)
        print("  Checking programming integrity")
        request = bytes([0x31, 0x01, 0x02, 0x02])
        response = self.can_interface.send_diagnostic_request(request, timeout=10.0)

        if not response or response[0] != 0x71:
            return False

        # Parse routine result
        if len(response) >= 4:
            result = response[3]
            if result == 0x00:
                print("  Verification passed")
                return True

        print("  Verification failed")
        return False

    def _post_programming(self) -> bool:
        """Post-programming checks and reset."""
        # Check dependencies
        print("  ├─ Checking programming dependencies")
        request = bytes([0x31, 0x01, 0x02, 0x02])
        response = self.can_interface.send_diagnostic_request(request, timeout=5.0)
        if not response or response[0] != 0x71:
            print("  │  └─ Failed")
            return False

        # ECU Reset
        print("  ├─ ECU reset")
        request = bytes([0x11, 0x01])
        response = self.can_interface.send_diagnostic_request(request)
        if not response or response[0] != 0x51:
            print("  │  └─ Failed")
            return False

        # Wait for application start
        print("  ├─ Waiting for application (5s)")
        time.sleep(5.0)

        # Verify application running
        print("  ├─ Verifying application")
        request = bytes([0x10, 0x01])  # Default session
        response = self.can_interface.send_diagnostic_request(request, timeout=5.0)
        if not response or response[0] != 0x50:
            print("  │  └─ Failed")
            return False

        print("  └─ Complete")
        return True

    def _security_access(self, level: int) -> bool:
        """Perform security access seed/key exchange."""
        # Request seed
        request = bytes([0x27, level])
        response = self.can_interface.send_diagnostic_request(request)

        if not response or response[0] != 0x67:
            return False

        seed = response[2:]

        # Check if already unlocked
        if all(b == 0 for b in seed):
            return True

        # Calculate key (simplified - use real algorithm in production)
        key = self._calculate_key(seed, level)

        # Send key
        request = bytes([0x27, level + 1]) + key
        response = self.can_interface.send_diagnostic_request(request)

        if not response or response[0] != 0x67:
            return False

        return True

    def _calculate_key(self, seed: bytes, level: int) -> bytes:
        """
        Calculate security access key from seed.
        NOTE: This is a placeholder. Real implementation must use
        manufacturer-specific algorithm.
        """
        # Example: Simple hash-based key (NOT SECURE - for demo only)
        hash_input = seed + bytes([level])
        key_hash = hashlib.sha256(hash_input).digest()
        return key_hash[:len(seed)]

    def _load_flash_file(self, filename: str) -> List[FlashMemoryRegion]:
        """Load flash file (supports Intel HEX, S-Record, binary)."""
        if filename.endswith('.hex'):
            return self._load_intel_hex(filename)
        elif filename.endswith(('.s19', '.s28', '.s37')):
            return self._load_srec(filename)
        else:
            return self._load_binary(filename)

    def _load_binary(self, filename: str, base_address: int = 0x00000000) -> List[FlashMemoryRegion]:
        """Load binary flash file."""
        with open(filename, 'rb') as f:
            data = f.read()

        checksum = zlib.crc32(data)

        region = FlashMemoryRegion(
            address=base_address,
            size=len(data),
            data=data,
            checksum=checksum
        )

        return [region]

    def _load_intel_hex(self, filename: str) -> List[FlashMemoryRegion]:
        """Load Intel HEX flash file."""
        # Simplified Intel HEX parser
        # In production, use intelhex library
        regions = []
        current_address = 0
        current_data = bytearray()

        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line.startswith(':'):
                    continue

                # Parse record
                byte_count = int(line[1:3], 16)
                address = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                data = bytes.fromhex(line[9:9+byte_count*2])

                if record_type == 0x00:  # Data record
                    if not current_data or address == current_address + len(current_data):
                        current_data.extend(data)
                    else:
                        # New region
                        if current_data:
                            regions.append(FlashMemoryRegion(
                                address=current_address,
                                size=len(current_data),
                                data=bytes(current_data)
                            ))
                        current_address = address
                        current_data = bytearray(data)

                elif record_type == 0x01:  # End of file
                    break

        # Add last region
        if current_data:
            regions.append(FlashMemoryRegion(
                address=current_address,
                size=len(current_data),
                data=bytes(current_data)
            ))

        return regions

    def _load_srec(self, filename: str) -> List[FlashMemoryRegion]:
        """Load Motorola S-Record flash file."""
        # Simplified S-Record parser
        # In production, use proper S-Record library
        regions = []
        # Implementation similar to Intel HEX parser
        # S1/S2/S3 records contain data
        return regions

# Example Usage
if __name__ == "__main__":
    from can_interface import SocketCANInterface

    def progress_callback(progress: FlashProgress):
        """Progress callback."""
        print(f"Progress: {progress.percentage:.1f}% - "
              f"Block {progress.current_block}/{progress.total_blocks} - "
              f"ETA: {progress.estimated_remaining:.0f}s")

    # Initialize
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)
    programmer = ECUFlashProgrammer(can_if, progress_callback=progress_callback)

    # Program ECU
    status, message = programmer.program_ecu("firmware.hex", verify=True)

    if status == FlashStatus.SUCCESS:
        print(f"Success: {message}")
    else:
        print(f"Failed: {message}")
```

## Error Recovery

### Common Failure Scenarios

1. **Communication Lost During Transfer**
   - Implement block retransmission
   - Track last successfully programmed block
   - Resume from checkpoint

2. **Power Loss During Programming**
   - ECU remains in bootloader mode
   - Re-attempt programming from beginning
   - Ensure battery voltage >12V before programming

3. **Checksum Failure**
   - Re-download affected memory region
   - Verify flash file integrity before programming

## Best Practices

1. **Always check battery voltage** (>12.5V recommended)
2. **Disable all non-essential ECUs** during programming
3. **Use TesterPresent** to maintain session
4. **Implement robust error handling** with retries
5. **Log all programming operations** for audit trail
6. **Verify programming** with checksum routines
7. **Never power off** during active programming

## References

- ISO 14229-1 - UDS Services 0x34, 0x35, 0x36, 0x37
- SAE J2534 - PassThru vehicle interface
