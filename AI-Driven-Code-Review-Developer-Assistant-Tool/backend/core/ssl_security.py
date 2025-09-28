import ssl
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import certifi
import OpenSSL
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import subprocess
import os

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class SSLSecurityManager:
    """SSL/TLS security management and validation."""

    def __init__(self):
        self.required_tls_version = ssl.TLSVersion.TLSv1_2
        self.preferred_ciphers = [
            'ECDHE-RSA-AES256-GCM-SHA384',
            'ECDHE-RSA-AES128-GCM-SHA256',
            'ECDHE-RSA-AES256-SHA384',
            'ECDHE-RSA-AES128-SHA256',
            'AES256-GCM-SHA384',
            'AES128-GCM-SHA256',
        ]

    def create_secure_ssl_context(self, purpose: ssl.Purpose = ssl.Purpose.SERVER_AUTH) -> ssl.SSLContext:
        """Create a secure SSL context with hardened settings."""
        context = ssl.create_default_context(purpose)

        # Set minimum TLS version
        context.minimum_version = self.required_tls_version
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        # Disable insecure protocols and features
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.options |= ssl.OP_NO_COMPRESSION
        context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
        context.options |= ssl.OP_SINGLE_DH_USE
        context.options |= ssl.OP_SINGLE_ECDH_USE

        # Set secure cipher suites
        context.set_ciphers(':'.join(self.preferred_ciphers))

        # Enable hostname checking
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        return context

    def validate_certificate(self, cert_path: str) -> Dict[str, any]:
        """Validate SSL certificate and return detailed information."""
        try:
            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()

            # Parse certificate
            cert = x509.load_pem_x509_certificate(cert_data)

            # Extract certificate information
            cert_info = {
                'valid': True,
                'subject': self._extract_subject_info(cert),
                'issuer': self._extract_issuer_info(cert),
                'serial_number': str(cert.serial_number),
                'not_before': cert.not_valid_before,
                'not_after': cert.not_valid_after,
                'signature_algorithm': cert.signature_algorithm_oid._name,
                'public_key_size': cert.public_key().key_size,
                'san_names': self._extract_san_names(cert),
                'key_usage': self._extract_key_usage(cert),
                'warnings': [],
                'errors': []
            }

            # Validate certificate expiration
            now = datetime.utcnow()
            if cert.not_valid_after < now:
                cert_info['errors'].append('Certificate has expired')
                cert_info['valid'] = False
            elif cert.not_valid_after < now + timedelta(days=30):
                cert_info['warnings'].append('Certificate expires within 30 days')

            # Validate certificate not yet valid
            if cert.not_valid_before > now:
                cert_info['errors'].append('Certificate is not yet valid')
                cert_info['valid'] = False

            # Check key size
            if cert_info['public_key_size'] < 2048:
                cert_info['errors'].append('Public key size is too small (minimum 2048 bits)')
                cert_info['valid'] = False

            # Check signature algorithm
            weak_algorithms = ['md5', 'sha1']
            if any(alg in cert_info['signature_algorithm'].lower() for alg in weak_algorithms):
                cert_info['errors'].append(f'Weak signature algorithm: {cert_info["signature_algorithm"]}')
                cert_info['valid'] = False

            return cert_info

        except Exception as e:
            logger.error(f"Certificate validation error: {e}")
            return {
                'valid': False,
                'errors': [f'Certificate validation failed: {str(e)}']
            }

    def _extract_subject_info(self, cert: x509.Certificate) -> Dict[str, str]:
        """Extract subject information from certificate."""
        subject_info = {}
        for attribute in cert.subject:
            subject_info[attribute.oid._name] = attribute.value
        return subject_info

    def _extract_issuer_info(self, cert: x509.Certificate) -> Dict[str, str]:
        """Extract issuer information from certificate."""
        issuer_info = {}
        for attribute in cert.issuer:
            issuer_info[attribute.oid._name] = attribute.value
        return issuer_info

    def _extract_san_names(self, cert: x509.Certificate) -> List[str]:
        """Extract Subject Alternative Names from certificate."""
        try:
            san_extension = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            return [name.value for name in san_extension.value]
        except x509.ExtensionNotFound:
            return []

    def _extract_key_usage(self, cert: x509.Certificate) -> List[str]:
        """Extract key usage from certificate."""
        try:
            key_usage_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
            key_usage = key_usage_ext.value

            usages = []
            if key_usage.digital_signature:
                usages.append('digital_signature')
            if key_usage.key_encipherment:
                usages.append('key_encipherment')
            if key_usage.key_agreement:
                usages.append('key_agreement')

            return usages
        except x509.ExtensionNotFound:
            return []

    def check_ssl_configuration(self, hostname: str, port: int = 443) -> Dict[str, any]:
        """Check SSL configuration of a remote host."""
        try:
            context = self.create_secure_ssl_context()

            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert_chain()[0]
                    cert_pem = ssl.DER_cert_to_PEM_cert(cert_der)

                    ssl_info = {
                        'protocol': ssock.version(),
                        'cipher': ssock.cipher(),
                        'compression': ssock.compression(),
                        'certificate': cert_pem,
                        'cert_validation': self.validate_certificate_string(cert_pem),
                        'security_score': 0
                    }

                    # Calculate security score
                    ssl_info['security_score'] = self._calculate_ssl_score(ssl_info)

                    return ssl_info

        except Exception as e:
            logger.error(f"SSL configuration check failed for {hostname}:{port}: {e}")
            return {
                'error': str(e),
                'security_score': 0
            }

    def validate_certificate_string(self, cert_pem: str) -> Dict[str, any]:
        """Validate certificate from PEM string."""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())

            # Basic validation
            now = datetime.utcnow()
            is_valid = (cert.not_valid_before <= now <= cert.not_valid_after)

            return {
                'valid': is_valid,
                'not_before': cert.not_valid_before.isoformat(),
                'not_after': cert.not_valid_after.isoformat(),
                'days_until_expiry': (cert.not_valid_after - now).days
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

    def _calculate_ssl_score(self, ssl_info: Dict[str, any]) -> int:
        """Calculate SSL security score (0-100)."""
        score = 100

        # Check protocol version
        protocol = ssl_info.get('protocol', '')
        if protocol in ['TLSv1.3']:
            score += 0  # Perfect
        elif protocol in ['TLSv1.2']:
            score -= 10
        elif protocol in ['TLSv1.1', 'TLSv1']:
            score -= 40
        else:
            score -= 60

        # Check cipher strength
        cipher_info = ssl_info.get('cipher', [])
        if cipher_info:
            cipher_name = cipher_info[0] if isinstance(cipher_info, tuple) else str(cipher_info)
            if 'AES256-GCM' in cipher_name:
                score += 0  # Perfect
            elif 'AES128-GCM' in cipher_name:
                score -= 5
            elif 'AES' in cipher_name:
                score -= 15
            else:
                score -= 30

        # Check certificate validity
        cert_validation = ssl_info.get('cert_validation', {})
        if not cert_validation.get('valid', False):
            score -= 50

        # Check certificate expiry
        days_until_expiry = cert_validation.get('days_until_expiry', 0)
        if days_until_expiry < 7:
            score -= 30
        elif days_until_expiry < 30:
            score -= 15

        return max(0, min(100, score))

class CertificateManager:
    """Certificate management and automation."""

    def __init__(self):
        self.cert_directory = "/etc/ssl/certs/"
        self.key_directory = "/etc/ssl/private/"

    def generate_self_signed_certificate(
        self,
        hostname: str,
        country: str = "US",
        state: str = "CA",
        city: str = "San Francisco",
        organization: str = "CodeGenius AI",
        validity_days: int = 365
    ) -> Tuple[str, str]:
        """Generate self-signed certificate for development."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, city),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])

            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(hostname),
                    x509.DNSName(f"www.{hostname}"),
                    x509.DNSName("localhost"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())

            # Serialize to PEM format
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()

            return cert_pem, key_pem

        except Exception as e:
            logger.error(f"Failed to generate self-signed certificate: {e}")
            raise

    def setup_lets_encrypt_certificate(self, domain: str, email: str) -> bool:
        """Set up Let's Encrypt certificate using certbot."""
        try:
            # Check if certbot is installed
            result = subprocess.run(['which', 'certbot'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Certbot is not installed")
                return False

            # Run certbot to obtain certificate
            cmd = [
                'certbot', 'certonly',
                '--webroot',
                '--webroot-path=/var/www/html',
                '--email', email,
                '--agree-tos',
                '--no-eff-email',
                '--domains', domain
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Successfully obtained Let's Encrypt certificate for {domain}")
                return True
            else:
                logger.error(f"Failed to obtain Let's Encrypt certificate: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Let's Encrypt setup failed: {e}")
            return False

    def check_certificate_renewal(self, cert_path: str) -> bool:
        """Check if certificate needs renewal."""
        ssl_manager = SSLSecurityManager()
        cert_info = ssl_manager.validate_certificate(cert_path)

        if not cert_info.get('valid', False):
            return True

        # Check if certificate expires within 30 days
        not_after = cert_info.get('not_after')
        if not_after and isinstance(not_after, datetime):
            days_until_expiry = (not_after - datetime.utcnow()).days
            return days_until_expiry <= 30

        return False

    def renew_lets_encrypt_certificate(self, domain: str) -> bool:
        """Renew Let's Encrypt certificate."""
        try:
            cmd = ['certbot', 'renew', '--cert-name', domain, '--quiet']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Successfully renewed certificate for {domain}")
                return True
            else:
                logger.error(f"Certificate renewal failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Certificate renewal error: {e}")
            return False

class SecurityHeaders:
    """HTTP security headers management."""

    @staticmethod
    def get_security_headers(is_production: bool = True) -> Dict[str, str]:
        """Get comprehensive security headers."""
        headers = {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',

            # Prevent clickjacking
            'X-Frame-Options': 'DENY',

            # XSS protection
            'X-XSS-Protection': '1; mode=block',

            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',

            # Permissions policy
            'Permissions-Policy': (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), '
                'accelerometer=(), gyroscope=()'
            ),

            # Content Security Policy
            'Content-Security-Policy': SecurityHeaders._get_csp_header(is_production),
        }

        # Add HSTS only in production with HTTPS
        if is_production:
            headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )

        return headers

    @staticmethod
    def _get_csp_header(is_production: bool) -> str:
        """Generate Content Security Policy header."""
        if is_production:
            return (
                "default-src 'self'; "
                "script-src 'self' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com; "
                "frame-src https://js.stripe.com https://hooks.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            )
        else:
            # More permissive for development
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' https://api.stripe.com ws: wss:; "
                "frame-src https://js.stripe.com https://hooks.stripe.com;"
            )

def validate_ssl_setup() -> Dict[str, any]:
    """Validate SSL/TLS setup and configuration."""
    ssl_manager = SSLSecurityManager()
    results = {
        'ssl_configured': False,
        'certificate_valid': False,
        'security_score': 0,
        'issues': [],
        'recommendations': []
    }

    # Check if SSL certificates exist
    cert_paths = [
        '/etc/ssl/certs/fullchain.pem',
        'nginx/ssl/fullchain.pem',
        './ssl/fullchain.pem'
    ]

    cert_found = False
    for cert_path in cert_paths:
        if os.path.exists(cert_path):
            cert_found = True
            cert_info = ssl_manager.validate_certificate(cert_path)

            results['certificate_valid'] = cert_info.get('valid', False)
            results['certificate_info'] = cert_info

            if cert_info.get('errors'):
                results['issues'].extend(cert_info['errors'])
            if cert_info.get('warnings'):
                results['recommendations'].extend(cert_info['warnings'])

            break

    if not cert_found:
        results['issues'].append('No SSL certificate found')
        results['recommendations'].append('Configure SSL certificate for production')

    # Check if running in production without HTTPS
    if not settings.debug and not cert_found:
        results['issues'].append('Production environment without SSL certificate')

    # Calculate overall security score
    if results['certificate_valid']:
        results['security_score'] = 85
    elif cert_found:
        results['security_score'] = 50
    else:
        results['security_score'] = 0

    results['ssl_configured'] = cert_found and results['certificate_valid']

    return results