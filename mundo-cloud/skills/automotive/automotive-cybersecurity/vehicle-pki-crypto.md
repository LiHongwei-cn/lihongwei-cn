# Vehicle PKI & Cryptography Skill

## Overview

Expert skill for implementing PKI (Public Key Infrastructure) in automotive systems. Covers V2X certificate management, HSM key storage, cryptographic algorithms (AES-256, RSA-4096, ECDSA), secure key provisioning, and certificate lifecycle management.

## Core Competencies

### PKI Architecture
- **Certificate Authority (CA) Hierarchy**: Root CA → Enrollment CA → Pseudonym CA
- **V2X Certificates**: IEEE 1609.2, ETSI TS 103 097 standards
- **Certificate Provisioning**: Factory provisioning, enrollment protocols
- **Certificate Lifecycle**: Issuance, renewal, revocation (CRL/OCSP)
- **HSM Integration**: Secure key generation and storage

### Cryptographic Standards
- **Symmetric**: AES-256-GCM, ChaCha20-Poly1305
- **Asymmetric**: RSA-4096, ECDSA-P256/P384, EdDSA
- **Hash**: SHA-256, SHA-384, SHA-3
- **Key Exchange**: ECDH, X25519
- **TLS**: TLS 1.3 with perfect forward secrecy

## V2X PKI Implementation (IEEE 1609.2)

### Certificate Structure

```python
#!/usr/bin/env python3
"""
IEEE 1609.2 V2X Certificate Implementation
Supports US (SCMS) and EU (CCMS) PKI architectures
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from datetime import datetime, timedelta
import struct

class V2XCertificate:
    """IEEE 1609.2 Certificate for V2V/V2I communication"""

    def __init__(self, cert_type: str):
        """
        Initialize V2X certificate
        cert_type: "enrollment", "application", "pseudonym"
        """
        self.cert_type = cert_type
        self.private_key = None
        self.certificate = None
        self.cert_chain = []

    def generate_enrollment_certificate(self, ca_cert, ca_key, vehicle_id: str):
        """
        Generate long-term enrollment certificate (valid 3-5 years)
        Used to request pseudonym certificates from PCA
        """
        print(f"\n=== Generating Enrollment Certificate for {vehicle_id} ===")

        # Generate key pair (ECDSA P-256 for V2X)
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SCMS"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Enrollment"),
            x509.NameAttribute(NameOID.COMMON_NAME, vehicle_id),
        ])

        # Certificate valid for 3 years
        valid_from = datetime.utcnow()
        valid_to = valid_from + timedelta(days=3*365)

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(ca_cert.subject)
        builder = builder.public_key(self.private_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_to)

        # Add extensions
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True
        )

        # Sign certificate
        self.certificate = builder.sign(ca_key, hashes.SHA256(), default_backend())

        print(f"[INFO] Enrollment certificate generated")
        print(f"[INFO] Serial: {self.certificate.serial_number}")
        print(f"[INFO] Valid: {valid_from} to {valid_to}")
        print(f"[INFO] Subject: {vehicle_id}")

        return self.certificate

    def generate_pseudonym_certificate(self, pca_cert, pca_key, duration_weeks: int = 1):
        """
        Generate short-term pseudonym certificate (valid 1 week)
        Used for actual V2X communication to preserve privacy
        """
        print(f"\n=== Generating Pseudonym Certificate (valid {duration_weeks} weeks) ===")

        # Generate ephemeral key pair
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Pseudonym certificates use opaque identifiers, not vehicle ID
        pseudonym_id = f"PSID-{x509.random_serial_number():016X}"

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SCMS"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Pseudonym"),
            x509.NameAttribute(NameOID.COMMON_NAME, pseudonym_id),
        ])

        valid_from = datetime.utcnow()
        valid_to = valid_from + timedelta(weeks=duration_weeks)

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(pca_cert.subject)
        builder = builder.public_key(self.private_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_to)

        # Add V2X-specific extensions
        builder = builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        )

        # Application permissions (Service-Specific Permissions)
        # Example: CAM (Cooperative Awareness Message), DENM (Decentralized Environmental Notification)
        # Real implementation would use IEEE 1609.2 ASN.1 structures
        builder = builder.add_extension(
            x509.UnrecognizedExtension(
                x509.ObjectIdentifier("1.2.840.10045.2.1"),  # Example OID
                b'\x01\x02\x03\x04'  # SSP bitmask
            ),
            critical=False
        )

        self.certificate = builder.sign(pca_key, hashes.SHA256(), default_backend())

        print(f"[INFO] Pseudonym certificate generated")
        print(f"[INFO] Serial: {self.certificate.serial_number}")
        print(f"[INFO] PSID: {pseudonym_id}")
        print(f"[INFO] Valid: {valid_from} to {valid_to}")

        return self.certificate

    def export_certificate_chain(self, output_path: str):
        """Export certificate with full chain in PEM format"""
        with open(output_path, 'wb') as f:
            # Leaf certificate
            f.write(self.certificate.public_bytes(serialization.Encoding.PEM))

            # Intermediate certificates
            for cert in self.cert_chain:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[INFO] Certificate chain exported: {output_path}")

    def export_private_key_encrypted(self, output_path: str, password: bytes):
        """Export private key with encryption (for backup only - HSM preferred)"""
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password)
        )

        with open(output_path, 'wb') as f:
            f.write(pem)

        print(f"[WARN] Private key exported (encrypted): {output_path}")
        print(f"[WARN] Store in HSM for production use")


class V2XPKIManager:
    """Manage V2X PKI infrastructure"""

    def __init__(self):
        self.root_ca_cert = None
        self.root_ca_key = None
        self.enrollment_ca_cert = None
        self.enrollment_ca_key = None
        self.pseudonym_ca_cert = None
        self.pseudonym_ca_key = None

    def create_root_ca(self, common_name: str = "V2X Root CA"):
        """Create root CA (offline, air-gapped storage)"""
        print(f"\n=== Creating Root CA: {common_name} ===")

        # Generate RSA-4096 key (root CA uses RSA for broader compatibility)
        from cryptography.hazmat.primitives.asymmetric import rsa
        self.root_ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SCMS"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Root CA"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        valid_from = datetime.utcnow()
        valid_to = valid_from + timedelta(days=20*365)  # 20 years

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(issuer)
        builder = builder.public_key(self.root_ca_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_to)

        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=2),
            critical=True
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=False,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True
        )

        self.root_ca_cert = builder.sign(self.root_ca_key, hashes.SHA256(), default_backend())

        print(f"[INFO] Root CA created")
        print(f"[INFO] Valid for 20 years")
        print(f"[WARN] Store root CA private key in air-gapped HSM")

        return self.root_ca_cert

    def create_intermediate_ca(self, ca_type: str, common_name: str):
        """Create intermediate CA (Enrollment CA or Pseudonym CA)"""
        print(f"\n=== Creating {ca_type} CA: {common_name} ===")

        # Generate ECDSA P-384 key (intermediate CAs use ECC)
        ca_key = ec.generate_private_key(ec.SECP384R1(), default_backend())

        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SCMS"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, ca_type),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        valid_from = datetime.utcnow()
        valid_to = valid_from + timedelta(days=10*365)  # 10 years

        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(self.root_ca_cert.subject)
        builder = builder.public_key(ca_key.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(valid_from)
        builder = builder.not_valid_after(valid_to)

        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True
        )

        builder = builder.add_extension(
            x509.KeyUsage(
                digital_signature=False,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True
        )

        ca_cert = builder.sign(self.root_ca_key, hashes.SHA256(), default_backend())

        if ca_type == "Enrollment":
            self.enrollment_ca_cert = ca_cert
            self.enrollment_ca_key = ca_key
        elif ca_type == "Pseudonym":
            self.pseudonym_ca_cert = ca_cert
            self.pseudonym_ca_key = ca_key

        print(f"[INFO] {ca_type} CA created")
        print(f"[INFO] Valid for 10 years")

        return ca_cert, ca_key

# Example usage
def demo_v2x_pki():
    # Step 1: Create PKI hierarchy
    pki = V2XPKIManager()
    pki.create_root_ca("V2X SCMS Root CA")
    pki.create_intermediate_ca("Enrollment", "V2X Enrollment CA")
    pki.create_intermediate_ca("Pseudonym", "V2X Pseudonym CA")

    # Step 2: Vehicle enrollment
    vehicle = V2XCertificate("enrollment")
    enrollment_cert = vehicle.generate_enrollment_certificate(
        pki.enrollment_ca_cert,
        pki.enrollment_ca_key,
        vehicle_id="VIN-1HGBH41JXMN109186"
    )

    vehicle.export_certificate_chain("/tmp/vehicle_enrollment.pem")
    vehicle.export_private_key_encrypted("/tmp/vehicle_enrollment.key", b"SecurePassword123")

    # Step 3: Request pseudonym certificates (batch of 20)
    print("\n=== Requesting Pseudonym Certificate Batch ===")
    pseudonyms = []
    for i in range(20):
        psid_cert = V2XCertificate("pseudonym")
        psid_cert.generate_pseudonym_certificate(
            pki.pseudonym_ca_cert,
            pki.pseudonym_ca_key,
            duration_weeks=1
        )
        pseudonyms.append(psid_cert)

    print(f"[INFO] {len(pseudonyms)} pseudonym certificates generated")
    print(f"[INFO] Vehicle will rotate certificates weekly for privacy")

if __name__ == "__main__":
    demo_v2x_pki()
```

## HSM Integration for Key Storage

```python
#!/usr/bin/env python3
"""
HSM (Hardware Security Module) Integration
Secure key generation and cryptographic operations
Supports PKCS#11 interface (common in automotive HSMs)
"""

import os
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

class HSMInterface:
    """Interface to Hardware Security Module via PKCS#11"""

    def __init__(self, hsm_slot: int = 0, pin: str = "1234"):
        """
        Initialize HSM connection
        hsm_slot: Hardware slot ID (0-based)
        pin: User PIN for authentication
        """
        self.slot = hsm_slot
        self.pin = pin
        self.session = None

        print(f"=== HSM Initialization ===")
        print(f"[INFO] Slot: {hsm_slot}")

    def open_session(self):
        """Open HSM session"""
        # Real implementation would use PyKCS11 or python-pkcs11
        # Simulated for demonstration
        print(f"[INFO] Opening HSM session (Slot {self.slot})...")
        print(f"[INFO] Authenticating with PIN...")
        self.session = f"HSM_SESSION_{self.slot}"
        print(f"[PASS] HSM session opened")
        return True

    def generate_rsa_keypair(self, key_label: str, key_size: int = 4096, exportable: bool = False):
        """
        Generate RSA key pair in HSM
        key_label: Unique identifier for key
        key_size: 2048, 3072, or 4096
        exportable: Allow private key export (FALSE for production)
        """
        print(f"\n=== Generating RSA-{key_size} Key Pair in HSM ===")
        print(f"[INFO] Label: {key_label}")
        print(f"[WARN] Exportable: {exportable}")

        if exportable:
            print(f"[WARN] Exportable keys are security risk - use only for testing")

        # In real HSM:
        # - Key generation happens inside tamper-resistant hardware
        # - Private key never leaves HSM
        # - Only public key and key handle are returned

        # Simulate key generation
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        # Return key handle (not actual key)
        key_handle = f"HSM_KEY_{key_label}_{os.urandom(4).hex()}"

        print(f"[PASS] RSA key pair generated")
        print(f"[INFO] Key handle: {key_handle}")
        print(f"[INFO] Public key available for export")
        print(f"[INFO] Private key secured in HSM (non-exportable)")

        return key_handle, public_key

    def generate_ecc_keypair(self, key_label: str, curve: str = "P-256", exportable: bool = False):
        """
        Generate ECC key pair in HSM
        curve: "P-256", "P-384", or "P-521"
        """
        print(f"\n=== Generating ECC-{curve} Key Pair in HSM ===")
        print(f"[INFO] Label: {key_label}")

        curve_map = {
            "P-256": ec.SECP256R1(),
            "P-384": ec.SECP384R1(),
            "P-521": ec.SECP521R1()
        }

        private_key = ec.generate_private_key(curve_map[curve], default_backend())
        public_key = private_key.public_key()

        key_handle = f"HSM_KEY_{key_label}_{os.urandom(4).hex()}"

        print(f"[PASS] ECC key pair generated")
        print(f"[INFO] Key handle: {key_handle}")

        return key_handle, public_key

    def sign_data(self, key_handle: str, data: bytes, algorithm: str = "SHA256") -> bytes:
        """
        Sign data using HSM-stored private key
        Returns signature without exposing private key
        """
        print(f"\n=== HSM Signing Operation ===")
        print(f"[INFO] Key handle: {key_handle}")
        print(f"[INFO] Algorithm: {algorithm}")
        print(f"[INFO] Data size: {len(data)} bytes")

        # In real HSM:
        # - Data is sent to HSM
        # - HSM performs signature operation internally
        # - Only signature is returned

        # Simulate signing
        signature = os.urandom(512)  # RSA-4096 signature size

        print(f"[PASS] Signature generated ({len(signature)} bytes)")
        return signature

    def encrypt_data(self, key_handle: str, plaintext: bytes) -> bytes:
        """Encrypt data using HSM key"""
        print(f"\n=== HSM Encryption Operation ===")
        print(f"[INFO] Key handle: {key_handle}")
        print(f"[INFO] Plaintext size: {len(plaintext)} bytes")

        # Simulate AES-256-GCM encryption in HSM
        ciphertext = os.urandom(len(plaintext) + 16)  # +16 for GCM tag

        print(f"[PASS] Data encrypted ({len(ciphertext)} bytes)")
        return ciphertext

    def export_public_key(self, key_handle: str, output_path: str):
        """Export public key (private key remains in HSM)"""
        print(f"\n=== Exporting Public Key ===")
        print(f"[INFO] Key handle: {key_handle}")

        # Simulate public key export
        dummy_key = rsa.generate_private_key(65537, 4096, default_backend()).public_key()

        pem = dummy_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        with open(output_path, 'wb') as f:
            f.write(pem)

        print(f"[PASS] Public key exported: {output_path}")
        print(f"[INFO] Private key remains secured in HSM")

    def close_session(self):
        """Close HSM session"""
        print(f"\n[INFO] Closing HSM session...")
        self.session = None
        print(f"[PASS] HSM session closed")


# Example: Secure key provisioning flow
def demo_hsm_provisioning():
    hsm = HSMInterface(hsm_slot=0, pin="123456")
    hsm.open_session()

    # Generate enrollment key pair (long-term, non-exportable)
    enrollment_key_handle, enrollment_pubkey = hsm.generate_ecc_keypair(
        key_label="VEHICLE_ENROLLMENT_KEY",
        curve="P-256",
        exportable=False
    )

    # Export public key for CA signing
    hsm.export_public_key(enrollment_key_handle, "/tmp/enrollment_pubkey.pem")

    # Generate firmware signing key (OEM root of trust)
    fw_signing_key_handle, fw_pubkey = hsm.generate_rsa_keypair(
        key_label="OEM_FIRMWARE_SIGNING_KEY",
        key_size=4096,
        exportable=False
    )

    # Sign firmware image
    firmware_data = b"FIRMWARE_IMAGE_BINARY_DATA" * 1000
    signature = hsm.sign_data(fw_signing_key_handle, firmware_data, algorithm="SHA256")

    # Generate symmetric key for data encryption
    aes_key_handle, _ = hsm.generate_rsa_keypair(
        key_label="DATA_ENCRYPTION_KEY",
        key_size=256,  # Actually AES-256, not RSA
        exportable=False
    )

    # Encrypt telemetry data
    telemetry_data = b"VEHICLE_TELEMETRY_JSON_DATA"
    encrypted = hsm.encrypt_data(aes_key_handle, telemetry_data)

    hsm.close_session()

if __name__ == "__main__":
    demo_hsm_provisioning()
```

## Secure Key Provisioning (Factory)

```python
#!/usr/bin/env python3
"""
Secure Key Provisioning for Vehicle Manufacturing
Keys injected during production in secure facility
"""

import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class SecureKeyProvisioning:
    """Factory key injection system"""

    def __init__(self):
        self.master_key = None
        self.provisioned_devices = {}

    def load_master_key(self, master_key_path: str):
        """Load factory master key (HSM-backed)"""
        print("=== Loading Factory Master Key ===")
        # In production: master key stored in HSM, never exported
        self.master_key = secrets.token_bytes(32)  # AES-256
        print("[INFO] Master key loaded from HSM")

    def derive_device_key(self, vin: str) -> bytes:
        """Derive unique device key from VIN using KDF"""
        print(f"\n=== Deriving Device Key for VIN: {vin} ===")

        # HKDF (HMAC-based Key Derivation Function)
        salt = b"VEHICLE_KEY_DERIVATION_SALT"
        info = vin.encode('utf-8')

        # Simplified HKDF (use cryptography.hazmat.primitives.kdf.hkdf in production)
        prk = hashlib.pbkdf2_hmac('sha256', self.master_key, salt, 100000)
        okm = hashlib.pbkdf2_hmac('sha256', prk, info, 1)[:32]

        print(f"[INFO] Device key derived (32 bytes)")
        return okm

    def provision_vehicle(self, vin: str, ecu_serial: str):
        """Provision cryptographic keys to vehicle ECU"""
        print(f"\n=== Vehicle Key Provisioning ===")
        print(f"[INFO] VIN: {vin}")
        print(f"[INFO] ECU Serial: {ecu_serial}")

        # Derive unique device key
        device_key = self.derive_device_key(vin)

        # Generate enrollment private key
        from cryptography.hazmat.primitives.asymmetric import ec
        enrollment_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Encrypt private key with device key (for secure storage in ECU flash)
        encrypted_key = self._encrypt_key(enrollment_key, device_key)

        # Program to ECU secure storage
        provisioning_data = {
            "vin": vin,
            "ecu_serial": ecu_serial,
            "device_key_hash": hashlib.sha256(device_key).hexdigest(),
            "encrypted_enrollment_key": encrypted_key.hex(),
            "provisioning_timestamp": "2026-03-19T12:00:00Z"
        }

        self.provisioned_devices[vin] = provisioning_data

        print(f"[PASS] Vehicle provisioned successfully")
        print(f"[INFO] Keys stored in ECU secure flash")

        return provisioning_data

    def _encrypt_key(self, private_key, device_key: bytes) -> bytes:
        """Encrypt private key with device key using AES-256-GCM"""
        from cryptography.hazmat.primitives import serialization

        # Serialize private key
        key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Encrypt with AES-256-GCM
        iv = secrets.token_bytes(12)
        cipher = Cipher(
            algorithms.AES(device_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(key_bytes) + encryptor.finalize()

        # Return IV + ciphertext + tag
        return iv + ciphertext + encryptor.tag

# Example usage
def demo_factory_provisioning():
    provisioner = SecureKeyProvisioning()
    provisioner.load_master_key("/secure/master_key.bin")

    # Provision 3 vehicles
    vins = [
        "1HGBH41JXMN109186",
        "5YJSA1E26HF123456",
        "WBAJE5C59HG987654"
    ]

    for i, vin in enumerate(vins):
        provisioner.provision_vehicle(vin, f"ECU-TCU-{1000 + i}")

    print(f"\n=== Provisioning Complete ===")
    print(f"[INFO] {len(provisioner.provisioned_devices)} vehicles provisioned")

if __name__ == "__main__":
    demo_factory_provisioning()
```

## Certificate Revocation (CRL/OCSP)

```python
#!/usr/bin/env python3
"""
Certificate Revocation List (CRL) and OCSP Implementation
"""

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID
from datetime import datetime, timedelta

class CertificateRevocationManager:
    """Manage certificate revocation for V2X PKI"""

    def __init__(self, ca_cert, ca_key):
        self.ca_cert = ca_cert
        self.ca_key = ca_key
        self.revoked_certs = []

    def revoke_certificate(self, cert_serial: int, reason: str = "unspecified"):
        """Add certificate to revocation list"""
        print(f"\n=== Revoking Certificate ===")
        print(f"[INFO] Serial: {cert_serial}")
        print(f"[INFO] Reason: {reason}")

        revocation_date = datetime.utcnow()

        revoked_cert = x509.RevokedCertificateBuilder().serial_number(
            cert_serial
        ).revocation_date(
            revocation_date
        ).add_extension(
            x509.CRLReason(x509.ReasonFlags[reason]),
            critical=False
        ).build(default_backend())

        self.revoked_certs.append(revoked_cert)

        print(f"[PASS] Certificate revoked")

    def generate_crl(self, output_path: str):
        """Generate Certificate Revocation List"""
        print(f"\n=== Generating CRL ===")

        builder = x509.CertificateRevocationListBuilder()
        builder = builder.issuer_name(self.ca_cert.subject)
        builder = builder.last_update(datetime.utcnow())
        builder = builder.next_update(datetime.utcnow() + timedelta(days=7))

        for revoked_cert in self.revoked_certs:
            builder = builder.add_revoked_certificate(revoked_cert)

        crl = builder.sign(self.ca_key, hashes.SHA256(), default_backend())

        with open(output_path, 'wb') as f:
            f.write(crl.public_bytes(serialization.Encoding.PEM))

        print(f"[INFO] CRL generated: {output_path}")
        print(f"[INFO] Revoked certificates: {len(self.revoked_certs)}")
        print(f"[INFO] Valid until: {crl.next_update}")

        return crl

    def check_certificate_status(self, cert_serial: int) -> bool:
        """Check if certificate is revoked (OCSP-like check)"""
        for revoked_cert in self.revoked_certs:
            if revoked_cert.serial_number == cert_serial:
                print(f"[WARN] Certificate {cert_serial} is REVOKED")
                return False

        print(f"[PASS] Certificate {cert_serial} is VALID")
        return True

# Example usage
def demo_crl():
    # Create dummy CA
    from cryptography.hazmat.primitives.asymmetric import rsa

    ca_key = rsa.generate_private_key(65537, 4096, default_backend())
    ca_cert = x509.CertificateBuilder().subject_name(
        x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "Test CA")])
    ).issuer_name(
        x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "Test CA")])
    ).public_key(
        ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).sign(ca_key, hashes.SHA256(), default_backend())

    # Revoke compromised certificates
    crl_mgr = CertificateRevocationManager(ca_cert, ca_key)
    crl_mgr.revoke_certificate(12345678, reason="key_compromise")
    crl_mgr.revoke_certificate(87654321, reason="cessation_of_operation")

    # Generate CRL
    crl_mgr.generate_crl("/tmp/v2x_crl.pem")

    # Check status
    crl_mgr.check_certificate_status(12345678)  # Revoked
    crl_mgr.check_certificate_status(99999999)  # Valid

if __name__ == "__main__":
    demo_crl()
```

## Best Practices

1. **Key Storage**: Always use HSM for private keys in production
2. **Certificate Rotation**: Rotate pseudonym certificates weekly for privacy
3. **CRL Distribution**: Use CDN for CRL distribution, OCSP for real-time checks
4. **Algorithm Selection**: Use ECC (P-256/P-384) for constrained devices, RSA-4096 for CAs
5. **Quantum Readiness**: Plan migration to post-quantum algorithms (CRYSTALS-Dilithium)

## References

- IEEE 1609.2: Security Services for V2V/V2I Communications
- ETSI TS 103 097: Security Header and Certificate Formats
- ISO 21434: Cybersecurity Engineering
- NIST SP 800-57: Key Management Recommendations
