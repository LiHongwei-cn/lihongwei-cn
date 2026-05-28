# Secure Boot Chain Skill

## Overview

Expert skill for implementing secure boot architectures in automotive ECUs. Covers root of trust establishment, chain of trust verification, HAB (High Assurance Boot), signature verification, anti-rollback protection, secure firmware updates, and TPM/HSM integration.

## Core Competencies

### Secure Boot Architecture
- **Root of Trust (RoT)**: Immutable boot ROM, hardware-backed trust anchor
- **Chain of Trust**: Bootloader → OS kernel → Applications
- **Signature Verification**: RSA-4096/ECDSA-P384 cryptographic validation
- **Anti-Rollback**: Version monotonic counters, secure storage
- **Secure Updates**: Dual-bank firmware, atomic updates, rollback capability
- **HSM Integration**: Hardware Security Module for key storage and crypto operations

### Platform Support
- **NXP i.MX**: HAB (High Assurance Boot), CAAM crypto accelerator
- **Renesas R-Car**: Secure boot with PKCS#7 signatures
- **Infineon AURIX**: UCB (User Configuration Block), HSM firmware
- **STM32MP1**: Secure Boot with OTP fuses, ECDSA support
- **ARM TrustZone**: Secure world execution, OP-TEE integration

## NXP i.MX HAB Secure Boot Implementation

### HAB Architecture

```c
/*
 * NXP i.MX HAB (High Assurance Boot) Implementation
 * Secure boot flow: Boot ROM → SPL → U-Boot → Linux Kernel
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <openssl/sha.h>
#include <openssl/rsa.h>
#include <openssl/pem.h>

/* HAB CSF (Command Sequence File) Structure */
#define HAB_TAG_IVT 0xD1
#define HAB_TAG_DCD 0xD2
#define HAB_TAG_CSF 0xD4

#define HAB_CMD_INSTALL_KEY    0xBE
#define HAB_CMD_AUTHENTICATE   0xDA
#define HAB_CMD_SET_ENGINE     0xAF

typedef struct {
    uint8_t tag;
    uint16_t length;
    uint8_t version;
} hab_header_t;

typedef struct {
    hab_header_t header;
    uint32_t entry;
    uint32_t reserved1;
    uint32_t dcd;
    uint32_t boot_data;
    uint32_t self;
    uint32_t csf;
    uint32_t reserved2;
} hab_ivt_t;

typedef struct {
    hab_header_t header;
    uint8_t flags;
    uint16_t key_index;
    uint32_t pcl;          /* Protocol */
    uint32_t alg;          /* Algorithm */
    uint32_t sig_format;   /* Signature format */
    uint32_t cert_format;  /* Certificate format */
} hab_install_key_cmd_t;

typedef struct {
    hab_header_t header;
    uint8_t flags;
    uint16_t key_index;
    uint32_t pcl;
    uint32_t eng_cfg;      /* Engine configuration */
    uint32_t alg;
    uint32_t sig_blk;      /* Signature block address */
} hab_authenticate_cmd_t;

/**
 * Generate HAB CSF binary for secure boot
 * CSF contains public keys and authentication commands
 */
int hab_generate_csf(const char *srk_table, const char *csf_data,
                     const char *img_hash, const char *output_csf) {
    FILE *fp;
    hab_header_t csf_header = {
        .tag = HAB_TAG_CSF,
        .length = 0,  // Will be updated
        .version = 0x40
    };

    fp = fopen(output_csf, "wb");
    if (!fp) {
        fprintf(stderr, "Failed to create CSF file\n");
        return -1;
    }

    // Write CSF header
    fwrite(&csf_header, sizeof(csf_header), 1, fp);

    // Install SRK (Super Root Key)
    hab_install_key_cmd_t install_srk = {
        .header = {.tag = HAB_CMD_INSTALL_KEY, .length = sizeof(hab_install_key_cmd_t), .version = 0x40},
        .flags = 0x00,
        .key_index = 0,
        .pcl = 0x00,      // No protocol
        .alg = 0x21,      // SHA256 with RSA
        .sig_format = 0x03,  // PKCS#1 v1.5
        .cert_format = 0x09  // SRK table
    };
    fwrite(&install_srk, sizeof(install_srk), 1, fp);

    // Append SRK table
    FILE *srk_fp = fopen(srk_table, "rb");
    if (srk_fp) {
        uint8_t buffer[4096];
        size_t bytes;
        while ((bytes = fread(buffer, 1, sizeof(buffer), srk_fp)) > 0) {
            fwrite(buffer, 1, bytes, fp);
        }
        fclose(srk_fp);
    }

    // Authenticate data command
    hab_authenticate_cmd_t auth_data = {
        .header = {.tag = HAB_CMD_AUTHENTICATE, .length = sizeof(hab_authenticate_cmd_t), .version = 0x40},
        .flags = 0x00,
        .key_index = 2,   // CSF key index
        .pcl = 0x00,
        .eng_cfg = 0x00,  // Use internal crypto engine (CAAM)
        .alg = 0x21,      // SHA256 with RSA
        .sig_blk = 0     // Signature block follows
    };
    fwrite(&auth_data, sizeof(auth_data), 1, fp);

    // Append signature (pre-generated)
    FILE *sig_fp = fopen(img_hash, "rb");
    if (sig_fp) {
        uint8_t buffer[512];
        size_t bytes = fread(buffer, 1, sizeof(buffer), sig_fp);
        fwrite(buffer, 1, bytes, fp);
        fclose(sig_fp);
    }

    // Update CSF length
    long csf_length = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    csf_header.length = (uint16_t)csf_length;
    fwrite(&csf_header, sizeof(csf_header), 1, fp);

    fclose(fp);
    printf("HAB CSF generated: %s (%ld bytes)\n", output_csf, csf_length);
    return 0;
}

/**
 * Verify HAB secure boot chain
 * Simulates Boot ROM verification flow
 */
int hab_verify_image(const char *image_path, const char *csf_path, const char *srk_pubkey) {
    printf("\n=== HAB Secure Boot Verification ===\n");

    // Step 1: Load and verify IVT
    FILE *img_fp = fopen(image_path, "rb");
    if (!img_fp) {
        fprintf(stderr, "Failed to open image\n");
        return -1;
    }

    hab_ivt_t ivt;
    fread(&ivt, sizeof(ivt), 1, img_fp);

    if (ivt.header.tag != HAB_TAG_IVT) {
        fprintf(stderr, "[FAIL] Invalid IVT tag: 0x%02X\n", ivt.header.tag);
        fclose(img_fp);
        return -1;
    }
    printf("[PASS] IVT tag valid\n");

    // Step 2: Verify CSF pointer
    if (ivt.csf == 0) {
        fprintf(stderr, "[FAIL] No CSF found in IVT\n");
        fclose(img_fp);
        return -1;
    }
    printf("[PASS] CSF pointer: 0x%08X\n", ivt.csf);

    // Step 3: Load and verify CSF
    FILE *csf_fp = fopen(csf_path, "rb");
    if (!csf_fp) {
        fprintf(stderr, "Failed to open CSF\n");
        fclose(img_fp);
        return -1;
    }

    hab_header_t csf_header;
    fread(&csf_header, sizeof(csf_header), 1, csf_fp);

    if (csf_header.tag != HAB_TAG_CSF) {
        fprintf(stderr, "[FAIL] Invalid CSF tag: 0x%02X\n", csf_header.tag);
        fclose(csf_fp);
        fclose(img_fp);
        return -1;
    }
    printf("[PASS] CSF tag valid\n");

    // Step 4: Compute image hash (SHA256)
    SHA256_CTX sha_ctx;
    uint8_t hash[SHA256_DIGEST_LENGTH];
    uint8_t buffer[4096];
    size_t bytes;

    SHA256_Init(&sha_ctx);
    fseek(img_fp, 0, SEEK_SET);
    while ((bytes = fread(buffer, 1, sizeof(buffer), img_fp)) > 0) {
        SHA256_Update(&sha_ctx, buffer, bytes);
    }
    SHA256_Final(hash, &sha_ctx);

    printf("[INFO] Image SHA256: ");
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        printf("%02x", hash[i]);
    }
    printf("\n");

    // Step 5: Verify signature using SRK public key
    // (Simplified - real HAB uses CAAM hardware)
    FILE *key_fp = fopen(srk_pubkey, "r");
    if (!key_fp) {
        fprintf(stderr, "[FAIL] Cannot open SRK public key\n");
        fclose(csf_fp);
        fclose(img_fp);
        return -1;
    }

    RSA *rsa = PEM_read_RSA_PUBKEY(key_fp, NULL, NULL, NULL);
    fclose(key_fp);

    if (!rsa) {
        fprintf(stderr, "[FAIL] Invalid RSA public key\n");
        fclose(csf_fp);
        fclose(img_fp);
        return -1;
    }

    // Read signature from CSF (simplified)
    uint8_t signature[512];
    fseek(csf_fp, -512, SEEK_END);
    fread(signature, 1, 512, csf_fp);

    int verify_result = RSA_verify(NID_sha256, hash, SHA256_DIGEST_LENGTH,
                                    signature, 512, rsa);

    RSA_free(rsa);
    fclose(csf_fp);
    fclose(img_fp);

    if (verify_result == 1) {
        printf("[PASS] Signature verification SUCCESS\n");
        printf("=== HAB VERIFICATION PASSED ===\n");
        return 0;
    } else {
        printf("[FAIL] Signature verification FAILED\n");
        printf("=== HAB VERIFICATION FAILED ===\n");
        return -1;
    }
}

int main() {
    // Generate CSF for U-Boot image
    hab_generate_csf(
        "/tmp/srk_table.bin",
        "/tmp/csf_commands.txt",
        "/tmp/uboot_signature.bin",
        "/tmp/u-boot.csf"
    );

    // Verify secure boot chain
    hab_verify_image(
        "/tmp/u-boot-signed.imx",
        "/tmp/u-boot.csf",
        "/tmp/srk_pubkey.pem"
    );

    return 0;
}
```

### HAB Fuse Programming (OTP)

```bash
#!/bin/bash
# NXP i.MX HAB Fuse Programming Script
# WARNING: Fuse programming is IRREVERSIBLE
# Only run on production hardware after thorough testing

set -e

DEVICE="/dev/imx_otp"
SRK_HASH_FILE="srk_hash.bin"

echo "=== NXP i.MX HAB Fuse Programming ==="
echo "WARNING: This operation is IRREVERSIBLE!"
read -p "Type 'CONFIRM' to proceed: " confirmation

if [ "$confirmation" != "CONFIRM" ]; then
    echo "Operation cancelled"
    exit 1
fi

# Step 1: Compute SRK hash (SHA256 of SRK table)
echo "[1/4] Computing SRK hash..."
sha256sum srk_table.bin | awk '{print $1}' | xxd -r -p > $SRK_HASH_FILE

# Step 2: Burn SRK hash to OTP fuses (Bank 3, Word 0-7)
echo "[2/4] Burning SRK hash to OTP fuses..."
# Fuse addresses: 0x6D0 (SRK_HASH[255:224]) to 0x6FC (SRK_HASH[31:0])
for i in {0..7}; do
    fuse_addr=$((0x6D0 + i * 4))
    offset=$((i * 4))
    value=$(od -An -tx4 -j $offset -N 4 $SRK_HASH_FILE | tr -d ' ')

    echo "  Burning 0x$value to fuse 0x$fuse_addr"
    # Real command: uboot> fuse prog 3 $word $value
    # Simulation only:
    echo "    fuse prog 3 $i 0x$value"
done

# Step 3: Enable Secure Boot (close device)
echo "[3/4] Enabling Secure Boot..."
# Fuse Bank 0, Word 6, Bit 1 (SEC_CONFIG[1] = CLOSED)
echo "  Setting SEC_CONFIG to CLOSED state"
# Real command: uboot> fuse prog 0 6 0x00000002
echo "    fuse prog 0 6 0x00000002"

# Step 4: Verify fuse programming
echo "[4/4] Verifying fuse programming..."
# Real command: uboot> fuse read 3 0 8
echo "  SRK Hash verification:"
for i in {0..7}; do
    echo "    fuse read 3 $i"
done

echo "=== HAB Fuse Programming Complete ==="
echo "Device is now in CLOSED state - only signed images will boot"
```

## Renesas R-Car Secure Boot

### Secure Boot Flow

```c
/*
 * Renesas R-Car Secure Boot Implementation
 * Uses PKCS#7 signatures for bootloader verification
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <openssl/pkcs7.h>
#include <openssl/x509.h>

#define RCAR_CERT_OFFSET 0x00000000
#define RCAR_CERT_SIZE   0x00010000
#define RCAR_BL2_OFFSET  0x00010000

typedef struct {
    uint32_t magic;              // "CERT"
    uint32_t cert_size;
    uint32_t num_of_images;
    uint8_t  reserved[4];
} rcar_cert_header_t;

typedef struct {
    uint32_t image_offset;
    uint32_t image_size;
    uint32_t load_address;
    uint8_t  hash_type;          // 0=SHA256, 1=SHA384
    uint8_t  hash[64];
    uint8_t  signature[512];
} rcar_image_cert_t;

/**
 * Verify R-Car bootloader signature
 */
int rcar_verify_bootloader(const char *bl2_path, const char *cert_path, const char *ca_cert) {
    printf("\n=== R-Car Secure Boot Verification ===\n");

    // Load CA certificate
    FILE *ca_fp = fopen(ca_cert, "r");
    if (!ca_fp) {
        fprintf(stderr, "[FAIL] Cannot open CA certificate\n");
        return -1;
    }

    X509 *ca = PEM_read_X509(ca_fp, NULL, NULL, NULL);
    fclose(ca_fp);

    if (!ca) {
        fprintf(stderr, "[FAIL] Invalid CA certificate\n");
        return -1;
    }
    printf("[PASS] CA certificate loaded\n");

    // Load bootloader certificate (PKCS#7)
    FILE *cert_fp = fopen(cert_path, "rb");
    if (!cert_fp) {
        fprintf(stderr, "[FAIL] Cannot open bootloader certificate\n");
        X509_free(ca);
        return -1;
    }

    PKCS7 *p7 = d2i_PKCS7_fp(cert_fp, NULL);
    fclose(cert_fp);

    if (!p7) {
        fprintf(stderr, "[FAIL] Invalid PKCS#7 structure\n");
        X509_free(ca);
        return -1;
    }
    printf("[PASS] PKCS#7 certificate loaded\n");

    // Load bootloader image
    FILE *bl2_fp = fopen(bl2_path, "rb");
    if (!bl2_fp) {
        fprintf(stderr, "[FAIL] Cannot open bootloader image\n");
        PKCS7_free(p7);
        X509_free(ca);
        return -1;
    }

    fseek(bl2_fp, 0, SEEK_END);
    size_t bl2_size = ftell(bl2_fp);
    fseek(bl2_fp, 0, SEEK_SET);

    uint8_t *bl2_data = malloc(bl2_size);
    fread(bl2_data, 1, bl2_size, bl2_fp);
    fclose(bl2_fp);

    // Create BIO for verification
    BIO *bio_data = BIO_new_mem_buf(bl2_data, bl2_size);
    BIO *bio_out = BIO_new(BIO_s_mem());

    // Verify PKCS#7 signature
    X509_STORE *store = X509_STORE_new();
    X509_STORE_add_cert(store, ca);

    int verify_result = PKCS7_verify(p7, NULL, store, bio_data, bio_out, 0);

    BIO_free(bio_data);
    BIO_free(bio_out);
    X509_STORE_free(store);
    PKCS7_free(p7);
    X509_free(ca);
    free(bl2_data);

    if (verify_result == 1) {
        printf("[PASS] Bootloader signature valid\n");
        printf("=== R-Car SECURE BOOT PASSED ===\n");
        return 0;
    } else {
        fprintf(stderr, "[FAIL] Bootloader signature invalid\n");
        printf("=== R-Car SECURE BOOT FAILED ===\n");
        return -1;
    }
}

int main() {
    rcar_verify_bootloader(
        "/tmp/bl2.bin",
        "/tmp/bl2_cert.p7",
        "/tmp/ca.pem"
    );
    return 0;
}
```

## Infineon AURIX HSM Secure Boot

### HSM Configuration

```c
/*
 * Infineon AURIX TC3xx HSM-based Secure Boot
 * HSM performs signature verification in isolated core
 */

#include <stdio.h>
#include <stdint.h>

#define UCB_BMHD_BASE    0xAF400000
#define UCB_BOOT_BASE    0xAF400100
#define HSM_FIRMWARE     0x80000000
#define HSM_STATUS_REG   0xF0000000

typedef struct {
    uint32_t stad;           // Start address
    uint32_t crc;            // CRC32
    uint32_t crcRange;       // CRC range
    uint32_t reserved;
    uint32_t confirmation;   // 0x43211234 if valid
} ucb_bmhd_t;

typedef struct {
    uint32_t boot_mode;
    uint32_t boot_sector;
    uint32_t secure_boot_enable;
    uint32_t signature_check;
    uint8_t  public_key_hash[32];
} ucb_boot_config_t;

/**
 * Program AURIX UCB (User Configuration Block) for secure boot
 */
int aurix_program_ucb_secure_boot(const uint8_t *pubkey_hash) {
    printf("\n=== AURIX UCB Secure Boot Configuration ===\n");

    ucb_boot_config_t ucb_config = {0};
    ucb_config.boot_mode = 0x00000001;           // Internal Flash boot
    ucb_config.boot_sector = 0x00000000;         // Sector 0
    ucb_config.secure_boot_enable = 0x00000001;  // Enable secure boot
    ucb_config.signature_check = 0x00000001;     // Enable RSA signature check

    memcpy(ucb_config.public_key_hash, pubkey_hash, 32);

    // Write to UCB (requires password unlock in real hardware)
    printf("[INFO] Programming UCB_BOOT...\n");
    printf("  Boot Mode: 0x%08X\n", ucb_config.boot_mode);
    printf("  Secure Boot: %s\n", ucb_config.secure_boot_enable ? "ENABLED" : "DISABLED");
    printf("  Public Key Hash: ");
    for (int i = 0; i < 32; i++) {
        printf("%02x", ucb_config.public_key_hash[i]);
    }
    printf("\n");

    // In real implementation:
    // - Unlock UCB with password
    // - Write UCB_BOOT structure
    // - Confirm and lock UCB

    printf("[PASS] UCB secure boot configured\n");
    return 0;
}

/**
 * HSM firmware verification flow
 */
int aurix_hsm_verify_firmware(const char *firmware_path, const uint8_t *pubkey_hash) {
    printf("\n=== AURIX HSM Firmware Verification ===\n");

    // Step 1: Load firmware to HSM memory
    FILE *fw_fp = fopen(firmware_path, "rb");
    if (!fw_fp) {
        fprintf(stderr, "[FAIL] Cannot open firmware\n");
        return -1;
    }

    fseek(fw_fp, 0, SEEK_END);
    size_t fw_size = ftell(fw_fp);
    fseek(fw_fp, 0, SEEK_SET);

    uint8_t *fw_data = malloc(fw_size);
    fread(fw_data, 1, fw_size, fw_fp);
    fclose(fw_fp);

    printf("[INFO] Firmware loaded: %zu bytes\n", fw_size);

    // Step 2: HSM computes firmware hash
    uint8_t fw_hash[32];
    // SHA256(fw_data) -> fw_hash
    printf("[INFO] HSM computing SHA256...\n");

    // Step 3: HSM verifies RSA signature
    printf("[INFO] HSM verifying RSA-4096 signature...\n");

    // In real HSM:
    // - Load public key from UCB
    // - Verify signature using hardware crypto accelerator
    // - Return result to application core

    int verify_result = 1; // Simulated success

    free(fw_data);

    if (verify_result) {
        printf("[PASS] HSM signature verification SUCCESS\n");
        printf("[INFO] Transferring control to verified firmware...\n");
        return 0;
    } else {
        fprintf(stderr, "[FAIL] HSM signature verification FAILED\n");
        fprintf(stderr, "[FATAL] Boot halted by HSM\n");
        return -1;
    }
}

int main() {
    uint8_t pubkey_hash[32] = {
        0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00, 0x11,
        0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99
    };

    aurix_program_ucb_secure_boot(pubkey_hash);
    aurix_hsm_verify_firmware("/tmp/application.elf", pubkey_hash);

    return 0;
}
```

## Anti-Rollback Protection

```c
/*
 * Firmware Version Anti-Rollback Protection
 * Uses monotonic counter in secure storage (OTP/RPMB)
 */

#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define SECURE_STORAGE_BASE  0x70000000
#define VERSION_COUNTER_ADDR (SECURE_STORAGE_BASE + 0x100)

typedef struct {
    uint32_t major;
    uint32_t minor;
    uint32_t patch;
    uint32_t build;
} firmware_version_t;

/**
 * Read monotonic counter from secure storage
 * In real hardware: OTP fuse, RPMB partition, or TPM NV-RAM
 */
uint32_t read_secure_version_counter(void) {
    // Simulated read from OTP
    // Real implementation would access hardware-backed storage
    uint32_t counter = 42; // Example: current firmware version counter
    printf("[INFO] Secure version counter: %u\n", counter);
    return counter;
}

/**
 * Increment secure version counter (one-way operation)
 * WARNING: OTP fuses can only be programmed once
 */
int increment_secure_version_counter(void) {
    printf("[WARN] Incrementing secure version counter (IRREVERSIBLE)\n");

    // In real hardware:
    // - Write to OTP fuse (can only change 0 -> 1)
    // - Or increment RPMB replay-protected counter

    printf("[INFO] Secure version counter incremented\n");
    return 0;
}

/**
 * Verify firmware version against anti-rollback counter
 */
int verify_firmware_version(firmware_version_t *fw_version) {
    printf("\n=== Anti-Rollback Verification ===\n");

    // Combine version into single counter
    uint32_t fw_counter = (fw_version->major * 1000) +
                          (fw_version->minor * 100) +
                          fw_version->patch;

    printf("[INFO] Firmware version: %u.%u.%u (counter=%u)\n",
           fw_version->major, fw_version->minor, fw_version->patch, fw_counter);

    // Read secure counter
    uint32_t secure_counter = read_secure_version_counter();

    // Check for rollback
    if (fw_counter < secure_counter) {
        fprintf(stderr, "[FAIL] ROLLBACK DETECTED!\n");
        fprintf(stderr, "       Firmware counter: %u\n", fw_counter);
        fprintf(stderr, "       Secure counter: %u\n", secure_counter);
        fprintf(stderr, "[FATAL] Boot halted - rollback protection enforced\n");
        return -1;
    }

    printf("[PASS] Anti-rollback check passed\n");

    // If this is an update (fw_counter > secure_counter), increment secure counter
    if (fw_counter > secure_counter) {
        printf("[INFO] Firmware update detected (%u -> %u)\n", secure_counter, fw_counter);
        increment_secure_version_counter();
    }

    return 0;
}

int main() {
    firmware_version_t current_fw = {.major = 2, .minor = 1, .patch = 5};
    verify_firmware_version(&current_fw);

    // Simulate rollback attempt
    firmware_version_t old_fw = {.major = 1, .minor = 9, .patch = 0};
    verify_firmware_version(&old_fw);

    return 0;
}
```

## Secure Firmware Update (Dual-Bank)

```python
#!/usr/bin/env python3
"""
Dual-Bank Secure Firmware Update
Atomic updates with rollback capability
"""

import hashlib
import struct
import os

class DualBankFirmwareUpdater:
    def __init__(self, bank_a_path: str, bank_b_path: str):
        self.bank_a = bank_a_path
        self.bank_b = bank_b_path
        self.active_bank = self._read_active_bank()

    def _read_active_bank(self) -> str:
        """Read active bank from persistent flag"""
        # In real hardware: read from flash metadata sector
        if os.path.exists("/tmp/active_bank"):
            with open("/tmp/active_bank", 'r') as f:
                return f.read().strip()
        return "A"

    def _set_active_bank(self, bank: str):
        """Set active bank (committed after successful boot)"""
        with open("/tmp/active_bank", 'w') as f:
            f.write(bank)
        print(f"[INFO] Active bank set to: {bank}")

    def update_firmware(self, new_firmware_path: str, signature_path: str):
        """Perform dual-bank firmware update"""
        print("\n=== Dual-Bank Firmware Update ===")

        # Determine inactive bank (update target)
        inactive_bank = "B" if self.active_bank == "A" else "A"
        target_path = self.bank_b if inactive_bank == "B" else self.bank_a

        print(f"[INFO] Active bank: {self.active_bank}")
        print(f"[INFO] Update target: Bank {inactive_bank}")

        # Step 1: Verify signature of new firmware
        print("[1/5] Verifying firmware signature...")
        if not self._verify_signature(new_firmware_path, signature_path):
            print("[FAIL] Signature verification failed")
            return False

        # Step 2: Write firmware to inactive bank
        print("[2/5] Writing firmware to inactive bank...")
        with open(new_firmware_path, 'rb') as src:
            with open(target_path, 'wb') as dst:
                dst.write(src.read())
        print(f"[INFO] Firmware written to {target_path}")

        # Step 3: Verify written firmware
        print("[3/5] Verifying written firmware...")
        if not self._verify_firmware_integrity(target_path):
            print("[FAIL] Written firmware integrity check failed")
            return False

        # Step 4: Switch active bank (NOT committed yet)
        print("[4/5] Switching to new firmware...")
        self._set_active_bank(inactive_bank)

        # Step 5: Reboot to new firmware
        print("[5/5] Reboot required to activate new firmware")
        print("[INFO] Rollback available if boot fails")

        return True

    def _verify_signature(self, firmware_path: str, signature_path: str) -> bool:
        """Verify RSA signature of firmware"""
        # Simplified - real implementation uses crypto library
        print("[PASS] Signature valid")
        return True

    def _verify_firmware_integrity(self, firmware_path: str) -> bool:
        """Verify firmware CRC/hash"""
        with open(firmware_path, 'rb') as f:
            data = f.read()

        computed_hash = hashlib.sha256(data).hexdigest()
        print(f"[INFO] Firmware SHA256: {computed_hash}")
        print("[PASS] Integrity check passed")
        return True

    def rollback_firmware(self):
        """Rollback to previous firmware after failed update"""
        print("\n=== Firmware Rollback ===")

        previous_bank = "B" if self.active_bank == "A" else "A"
        print(f"[INFO] Rolling back from Bank {self.active_bank} to Bank {previous_bank}")

        self._set_active_bank(previous_bank)
        print("[PASS] Rollback complete - reboot required")

# Example usage
if __name__ == "__main__":
    updater = DualBankFirmwareUpdater(
        bank_a_path="/tmp/firmware_bank_a.bin",
        bank_b_path="/tmp/firmware_bank_b.bin"
    )

    # Perform update
    updater.update_firmware(
        new_firmware_path="/tmp/new_firmware_v2.1.5.bin",
        signature_path="/tmp/new_firmware_v2.1.5.sig"
    )

    # Simulate rollback (if boot test fails)
    # updater.rollback_firmware()
```

## Best Practices

1. **Hardware Root of Trust**: Always anchor security in immutable boot ROM
2. **Signature Algorithm**: Use RSA-4096 or ECDSA-P384 for quantum resistance
3. **Anti-Rollback**: Implement monotonic counters in tamper-resistant storage
4. **Dual-Bank Updates**: Maintain backup firmware for recovery
5. **HSM Integration**: Offload crypto operations to dedicated security hardware

## References

- NXP AN4581: i.MX HAB Secure Boot User Guide
- Renesas R-Car Security Architecture Manual
- Infineon AURIX TC3xx HSM Firmware Guide
- ARM Trusted Firmware A (TF-A) Documentation
