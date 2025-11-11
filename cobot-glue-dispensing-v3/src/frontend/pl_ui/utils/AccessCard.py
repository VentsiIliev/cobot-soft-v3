"""
Digital Access Pass Generator

A professional library for generating digital passes compatible with
Google Wallet and Apple Wallet for machine access cards.
"""

import json
import zipfile
import hashlib
import os
import qrcode
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont

# Import the original User class
from modules.shared.shared.user.User import User, Role

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PassConfig:
    """Configuration for digital pass generation."""

    # Pass identification
    pass_type_identifier: str = "pass.com.company.access"
    team_identifier: str = "YOUR_TEAM_ID"
    organization_name: str = "Your Company Name"
    description: str = "Machine Access Card"

    # Visual design
    background_color: str = "rgb(79, 70, 229)"
    foreground_color: str = "rgb(255, 255, 255)"
    label_color: str = "rgb(248, 250, 252)"

    # Pass details
    logo_text: str = "MACHINE ACCESS"
    validity_days: int = 365

    # Logo
    logo_image_path: Optional[str] = None

    # Locations
    locations: list = None

    def __post_init__(self):
        if self.locations is None:
            self.locations = [
                {
                    "latitude": 42.3601,
                    "longitude": -71.0589,
                    "relevantText": "Welcome to the machine!"
                }
            ]


class DigitalPassGenerator:
    """Professional digital pass generator for mobile wallets."""

    def __init__(self, config: Optional[PassConfig] = None):
        self.config = config or PassConfig()
    
    def _generate_qr_code(self, user: User, serial_number: str) -> tuple[str, bytes]:
        """Generate QR code for access pass and return both base64 string and binary data."""
        qr_data = f"ACCESS:{user.email}:{serial_number}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for HTML
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        # Return binary data for .pkpass
        img_buffer.seek(0)
        qr_binary = img_buffer.getvalue()
        
        return qr_base64, qr_binary
    
    def _get_access_level(self, user: User) -> str:
        """Map user role to access level string."""
        role_access_map = {
            Role.ADMIN: "Full Machine Access",
            Role.OPERATOR: "Production Floor Access", 
            Role.SERVICE: "Service & Maintenance Access"
        }
        return role_access_map.get(user.role, "General Machine Access")

    def _generate_pass_json(self, user: User, serial_number: str) -> Dict[str, Any]:
        issue_date = datetime.now()
        expiration_date = issue_date + timedelta(days=self.config.validity_days)

        return {
            "formatVersion": 1,
            "passTypeIdentifier": self.config.pass_type_identifier,
            "serialNumber": serial_number,
            "teamIdentifier": self.config.team_identifier,
            "organizationName": self.config.organization_name,
            "description": self.config.description,
            "backgroundColor": self.config.background_color,
            "foregroundColor": self.config.foreground_color,
            "logoText": self.config.logo_text,
            "generic": {
                "primaryFields": [
                    {"key": "name", "label": "Name", "value": user.get_full_name()}
                ],
                "secondaryFields": [
                    {"key": "role", "label": "Role", "value": user.role.value},
                    {"key": "user_id", "label": "ID", "value": str(user.id).zfill(3)}
                ],
                "auxiliaryFields": [
                    {"key": "access_level", "label": "Access", "value": self._get_access_level(user)}
                ]
            },
            "expirationDate": expiration_date.isoformat(),
            "barcodes": [
                {
                    "message": f"id = {user.id} password = {user.password}",
                    "format": "PKBarcodeFormatQR",
                    "messageEncoding": "iso-8859-1"
                }
            ]
        }

    def _generate_manifest(self, files: Dict[str, bytes]) -> str:
        manifest = {}
        for filename, content in files.items():
            if filename != "manifest.json":
                sha1_hash = hashlib.sha1(content).hexdigest()
                manifest[filename] = sha1_hash
        return json.dumps(manifest, indent=2)

    def _create_signature(self, manifest_content: bytes) -> bytes:
        return hashlib.sha256(manifest_content + b"YOUR_SIGNING_KEY").digest()
    
    def _generate_default_logo(self) -> bytes:
        """Generate a simple default logo for the pass."""
        
        # Create a simple logo image
        size = (120, 120)
        img = Image.new('RGB', size, color=(79, 70, 229))  # Purple background
        draw = ImageDraw.Draw(img)
        
        # Draw "PL" text in the center
        try:
            # Try to use a better font if available
            font = ImageFont.truetype("arial.ttf", 48)
        except (OSError, IOError):
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Calculate text position to center it
        text = "PL"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # Draw white text
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Convert to bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()


    def create_digital_pass(
        self, user: User, output_path: str = "access_pass.pkpass", serial_number: Optional[str] = None
    ) -> tuple[str, str]:
        if not serial_number:
            serial_number = hashlib.md5(
                f"{user.get_full_name()}{user.email}{datetime.now()}".encode()
            ).hexdigest()[:12].upper()

        try:
            pass_json = self._generate_pass_json(user, serial_number)
            pass_json_bytes = json.dumps(pass_json, indent=2).encode('utf-8')

            files = {"pass.json": pass_json_bytes}

            try:
                qr_base64, qr_binary = self._generate_qr_code(user, serial_number)
                files["icon.png"] = qr_binary
                files["icon@2x.png"] = qr_binary
            except Exception as e:
                logger.warning(f"Could not generate QR code: {e}")

            if self.config.logo_image_path and os.path.exists(self.config.logo_image_path):
                try:
                    with open(self.config.logo_image_path, "rb") as f:
                        logo_data = f.read()
                        files["logo.png"] = logo_data
                        files["logo@2x.png"] = logo_data
                except Exception as e:
                    logger.warning(f"Could not load logo image: {e}")

            manifest_content = self._generate_manifest(files)
            manifest_bytes = manifest_content.encode('utf-8')
            files["manifest.json"] = manifest_bytes

            signature_bytes = self._create_signature(manifest_bytes)
            files["signature"] = signature_bytes

            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(output_path_obj, 'w', zipfile.ZIP_DEFLATED) as pkpass:
                for filename, content in files.items():
                    pkpass.writestr(filename, content)

            logger.info(f"Digital pass created successfully: {output_path}")

            google_pay_path = self._create_google_pay_json(
                pass_json, user, serial_number,
                str(output_path_obj).replace('.pkpass', '_google_pay.json')
            )

            return str(output_path_obj), google_pay_path

        except Exception as e:
            logger.error(f"Failed to create digital pass: {e}")
            raise

    def _create_google_pay_json(
        self, pass_data: Dict, user: User, serial_number: str, output_path: str
    ) -> str:
        google_pay_object = {
            "iss": "your-service-account-email@your-project.iam.gserviceaccount.com",
            "aud": "google",
            "typ": "savetowallet",
            "iat": int(datetime.now().timestamp()),
            "origins": [],
            "payload": {
                "genericObjects": [
                    {
                        "id": f"{self.config.pass_type_identifier}.{serial_number}",
                        "classId": f"{self.config.pass_type_identifier}",
                        "genericType": "GENERIC_TYPE_UNSPECIFIED",
                        "hexBackgroundColor": self.config.background_color.replace("rgb(", "#").replace(")", "").replace(", ", ""),
                        "logo": {"sourceUri": {"uri": "https://your-domain.com/logo.png"}},
                        "cardTitle": {"defaultValue": {"language": "en", "value": "Machine Access"}},
                        "subheader": {"defaultValue": {"language": "en", "value": user.get_full_name()}},
                        "header": {"defaultValue": {"language": "en", "value": self.config.organization_name}},
                        "barcode": {"type": "QR_CODE", "value": f"ACCESS:{user.email}:{serial_number}"},
                        "textModulesData": [
                            {"id": "email", "header": "Email", "body": user.email},
                            {"id": "employee_id", "header": "Employee ID", "body": serial_number},
                            {"id": "user_id", "header": "User ID", "body": user.id},
                            {"id": "role", "header": "Role", "body": user.role.value},
                            {"id": "access_level", "header": "Access Level", "body": self._get_access_level(user)}
                        ]
                    }
                ]
            }
        }

        with open(output_path, 'w') as f:
            json.dump(google_pay_object, f, indent=2)

        logger.info(f"Google Pay JSON created: {output_path}")
        return output_path


def create_access_pass_for_user(
    user: User, 
    config: Optional[PassConfig] = None,
    output_dir: str = "access_passes"
) -> tuple[str, str]:
    """
    Utility function to create access pass for an existing User instance.
    
    Args:
        user: User instance from shared.shared.user.User
        config: Optional PassConfig for customization
        output_dir: Directory to save the generated passes
        
    Returns:
        Tuple of (pkpass_path, google_pay_path)
    """
    if not config:
        config = PassConfig(
            organization_name="PL Project LTD.",
            description="Machine Access Pass",
            logo_text="PL PROJECT"
        )
    
    generator = DigitalPassGenerator(config)
    
    # Create output filename based on user info
    safe_name = f"{user.firstName}_{user.lastName}_{user.id}".replace(" ", "_")
    output_path = f"{output_dir}/{safe_name}_access_pass.pkpass"
    
    return generator.create_digital_pass(user, output_path)


def send_access_pass_email(user: User, pkpass_path: str, google_pay_path: str):
    """
    Send access pass via email to the user.
    
    Args:
        user: User instance
        pkpass_path: Path to the .pkpass file
        google_pay_path: Path to the Google Pay JSON file
    """
    try:
        from modules.shared.shared.email.emailSender import EmailSenderService, get_professional_email_template, get_default_email_config
        
        template = get_professional_email_template(
            user_name=user.get_full_name(),
            message=f"Here is your machine access pass. Your access level is: {DigitalPassGenerator()._get_access_level(user)}"
        )
        
        sender = EmailSenderService(config=get_default_email_config())
        
        sender.send_email(
            subject="Your Machine Access Pass",
            body=template,
            to_emails=[user.email] if user.email else [],
            html=True,
            attachments=[pkpass_path, google_pay_path]
        )
        
        logger.info(f"Access pass email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send access pass email: {e}")
        return False


def generate_printable_html_card(
    user: User,
    output_dir: str = "access_passes",
    config: Optional[PassConfig] = None
) -> str:
    """
    Generate a printable HTML access card for the user.
    
    Args:
        user: User instance from shared.shared.user.User
        output_dir: Directory to save the HTML file
        config: Optional PassConfig for customization
        
    Returns:
        Path to the generated HTML file
    """
    if not config:
        config = PassConfig(
            organization_name="PL Project LTD.",
            description="Machine Access Pass",
            logo_text="PL PROJECT"
        )
    
    # Generate serial number and QR code using shared function
    serial_number = hashlib.md5(
        f"{user.get_full_name()}{user.email}{datetime.now()}".encode()
    ).hexdigest()[:12].upper()
    
    # Use shared QR generation function
    generator = DigitalPassGenerator(config)
    qr_base64, qr_binary = generator._generate_qr_code(user, serial_number)
    
    # Get role-based access information  
    access_level = generator._get_access_level(user)
    
    # Calculate expiration date
    issue_date = datetime.now()
    expiration_date = issue_date + timedelta(days=config.validity_days)
    
    # Use original styling (purple/blue gradient) for all cards as in your template
    card_background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    role_icon = "⚙️"
    
    # Get user initials for photo placeholder
    initials = f"{user.firstName[0] if user.firstName else ''}{user.lastName[0] if user.lastName else ''}"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PL Project Employee Badge - {user.get_full_name()}</title>
    <style>
        @media print {{
            body {{ 
                margin: 0; 
                background: white !important; 
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .badge {{ 
                box-shadow: none !important; 
                page-break-inside: avoid;
                transform: none !important;
            }}
            .badge:hover {{
                transform: none !important;
            }}
            .holographic-effect {{
                display: none;
            }}
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}

        .badge-container {{
            perspective: 1000px;
        }}

        .badge {{
            width: 320px;
            height: 500px;
            background: {card_background};
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
            transform: rotateX(5deg) rotateY(-5deg);
            transition: all 0.3s ease;
        }}

        .badge:hover {{
            transform: rotateX(0deg) rotateY(0deg) scale(1.05);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        }}

        .badge-header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            position: relative;
        }}

        .company-logo {{
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #2c3e50, #3498db);
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 24px;
            color: white;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}

        .company-name {{
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }}

        .company-tagline {{
            font-size: 11px;
            color: #7f8c8d;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .employee-section {{
            padding: 30px 25px;
            color: white;
            text-align: center;
        }}

        .employee-photo {{
            width: 140px;
            height: 140px;
            border-radius: 15px;
            background: white;
            margin: 0 auto 20px;
            border: 4px solid rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}

        .employee-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}

        .employee-position {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 15px;
            font-weight: 500;
        }}

        .employee-id {{
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }}

        .access-level {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}

        .access-item {{
            flex: 1;
            text-align: center;
            padding: 8px 5px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            margin: 0 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .security-strip {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(90deg, #1abc9c, #16a085);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .security-text {{
            color: white;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .holographic-effect {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, 
                transparent 30%, 
                rgba(255, 255, 255, 0.1) 50%, 
                transparent 70%);
            pointer-events: none;
            animation: shimmer 3s infinite;
        }}

        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}

        .corner-accent {{
            position: absolute;
            width: 30px;
            height: 30px;
            background: rgba(255, 255, 255, 0.2);
        }}

        .corner-accent.top-left {{
            top: 0;
            left: 0;
            border-bottom-right-radius: 100%;
        }}

        .corner-accent.bottom-right {{
            bottom: 40px;
            right: 0;
            border-top-left-radius: 100%;
        }}

        .qr-image {{
            width: 120px;
            height: 120px;
            border-radius: 8px;
        }}

        .serial-number {{
            font-size: 10px;
            opacity: 0.8;
            font-family: monospace;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="badge-container">
        <div class="badge">
            <div class="corner-accent top-left"></div>
            <div class="corner-accent bottom-right"></div>
            <div class="holographic-effect"></div>
            
            <div class="badge-header">
                <div class="company-logo">PL</div>
                <div class="company-name">PL PROJECT</div>
                <div class="company-tagline">Revolution in Edge Dyeing Machines</div>
            </div>

            <div class="employee-section">
                <div class="employee-photo">
                    <img src="data:image/png;base64,{qr_base64}" alt="Access QR Code" class="qr-image">
                </div>
                <div class="employee-name">{user.get_full_name()}</div>
                <div class="employee-position">{user.role.value}</div>
                <div class="employee-id">ID: {str(user.id).zfill(3)}</div>
          

            </div>

            
        </div>
    </div>
</body>
</html>"""
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    safe_name = f"{user.firstName}_{user.lastName}_{user.id}".replace(" ", "_")
    html_path = f"{output_dir}/{safe_name}_printable_card.html"
    
    # Write HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Printable HTML card created: {html_path}")
    return html_path


def create_complete_access_package(
    user: User,
    config: Optional[PassConfig] = None,
    output_dir: str = "access_passes"
) -> tuple[str, str, str]:
    """
    Create a complete access package including digital passes and printable card.
    Uses shared QR code generation to ensure consistency across all formats.
    
    Args:
        user: User instance from shared.shared.user.User
        config: Optional PassConfig for customization
        output_dir: Directory to save all generated files
        
    Returns:
        Tuple of (pkpass_path, google_pay_path, html_card_path)
    """
    if not config:
        config = PassConfig()
    
    # Generate shared serial number and QR code once
    serial_number = hashlib.md5(
        f"{user.get_full_name()}{user.email}{datetime.now()}".encode()
    ).hexdigest()[:12].upper()
    
    generator = DigitalPassGenerator(config)
    qr_base64, qr_binary = generator._generate_qr_code(user, serial_number)
    
    # Create digital passes with shared serial number
    pkpass_path, google_pay_path = _create_access_pass_with_data(
        user=user,
        config=config,
        output_dir=output_dir,
        serial_number=serial_number,
        qr_binary=qr_binary
    )
    
    # Create printable HTML card with shared QR code
    html_card_path = _generate_printable_html_with_data(
        user=user,
        config=config,
        output_dir=output_dir,
        serial_number=serial_number,
        qr_base64=qr_base64
    )
    
    return pkpass_path, google_pay_path, html_card_path


import base64


def create_complete_access_package2(
        user: User,
        qr_code_path: str,  # NEW: external QR file path
        config: Optional[PassConfig] = None,
        output_dir: str = "access_passes"
) -> tuple[str, str, str]:
    """
    Create a complete access package including digital passes and printable card.
    Uses an externally provided QR code file for consistency across formats.

    Args:
        user: User instance from shared.shared.user.User
        qr_code_path: Path to an existing QR code PNG file
        config: Optional PassConfig for customization
        output_dir: Directory to save all generated files

    Returns:
        Tuple of (pkpass_path, google_pay_path, html_card_path)
    """
    if not config:
        config = PassConfig()

    # Generate shared serial number
    serial_number = hashlib.md5(
        f"{user.get_full_name()}{user.email}{datetime.now()}".encode()
    ).hexdigest()[:12].upper()

    # Load QR from file
    with open(qr_code_path, "rb") as f:
        qr_binary = f.read()
    qr_base64 = base64.b64encode(qr_binary).decode("utf-8")

    # Create digital passes with provided QR
    pkpass_path, google_pay_path = _create_access_pass_with_data(
        user=user,
        config=config,
        output_dir=output_dir,
        serial_number=serial_number,
        qr_binary=qr_binary
    )

    # Create printable HTML card with provided QR
    html_card_path = _generate_printable_html_with_data(
        user=user,
        config=config,
        output_dir=output_dir,
        serial_number=serial_number,
        qr_base64=qr_base64
    )

    return pkpass_path, google_pay_path, html_card_path


def _create_access_pass_with_data(
    user: User, config: PassConfig, output_dir: str, serial_number: str, qr_binary: bytes
) -> tuple[str, str]:
    """Create digital passes using pre-generated QR code and serial number."""
    generator = DigitalPassGenerator(config)
    
    # Manually set the QR data in the generator (bypass regeneration)
    output_path = os.path.join(output_dir, f"{user.get_full_name().replace(' ', '_')}_{str(user.id).zfill(3)}_access_pass.pkpass")
    
    pass_json = generator._generate_pass_json(user, serial_number)
    pass_json_bytes = json.dumps(pass_json, indent=2).encode('utf-8')
    
    files = {"pass.json": pass_json_bytes}
    files["icon.png"] = qr_binary
    files["icon@2x.png"] = qr_binary
    
    # Add logo if available
    if config.logo_image_path and os.path.exists(config.logo_image_path):
        with open(config.logo_image_path, "rb") as f:
            logo_data = f.read()
            files["logo.png"] = logo_data
            files["logo@2x.png"] = logo_data
    else:
        # Generate default logo
        logo_data = generator._generate_default_logo()
        files["logo.png"] = logo_data
        files["logo@2x.png"] = logo_data
    
    # Create manifest and signature
    manifest_json = generator._generate_manifest(files)
    files["manifest.json"] = manifest_json.encode('utf-8')
    files["signature"] = generator._create_signature(files["manifest.json"])
    
    # Create .pkpass file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as pkpass:
        for filename, content in files.items():
            pkpass.writestr(filename, content)
    
    logger.info(f"Digital pass created successfully: {output_path}")
    
    # Create Google Pay JSON
    google_pay_path = generator._create_google_pay_json(
        pass_json, user, serial_number,
        output_path.replace('.pkpass', '_google_pay.json')
    )
    
    return output_path, google_pay_path


def _generate_printable_html_with_data(
    user: User, config: PassConfig, output_dir: str, serial_number: str, qr_base64: str
) -> str:
    """Generate HTML card using pre-generated QR code and serial number."""
    generator = DigitalPassGenerator(config)
    access_level = generator._get_access_level(user)
    
    # Calculate expiration date
    issue_date = datetime.now()
    expiration_date = issue_date + timedelta(days=config.validity_days)
    
    # Use original styling (purple/blue gradient) for all cards as in your template
    card_background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    role_icon = "⚙️"
    
    # Get user initials for photo placeholder
    initials = f"{user.firstName[0] if user.firstName else ''}{user.lastName[0] if user.lastName else ''}"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PL Project Employee Badge - {user.get_full_name()}</title>
    <style>
        @media print {{
            body {{ 
                margin: 0; 
                background: white !important; 
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
            .badge {{ 
                box-shadow: none !important; 
                page-break-inside: avoid;
                transform: none !important;
            }}
            .badge:hover {{
                transform: none !important;
            }}
            .holographic-effect {{
                display: none;
            }}
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}

        .badge-container {{
            perspective: 1000px;
        }}

        .badge {{
            width: 320px;
            height: 500px;
            background: {card_background};
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
            transform: rotateX(5deg) rotateY(-5deg);
            transition: all 0.3s ease;
        }}

        .badge:hover {{
            transform: rotateX(0deg) rotateY(0deg) scale(1.05);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
        }}

        .badge-header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            text-align: center;
            position: relative;
        }}

        .company-logo {{
            width: 80px;
            height: 80px;
            background: linear-gradient(45deg, #2c3e50, #3498db);
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 24px;
            color: white;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}

        .company-name {{
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }}

        .company-tagline {{
            font-size: 11px;
            color: #7f8c8d;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .employee-section {{
            padding: 30px 25px;
            color: white;
            text-align: center;
        }}

        .employee-photo {{
            width: 140px;
            height: 140px;
            border-radius: 15px;
            background: white;
            margin: 0 auto 20px;
            border: 4px solid rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}

        .employee-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 8px;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}

        .employee-position {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 15px;
            font-weight: 500;
        }}

        .employee-id {{
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }}

        .access-level {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}

        .access-item {{
            flex: 1;
            text-align: center;
            padding: 8px 5px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            margin: 0 3px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .security-strip {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(90deg, #1abc9c, #16a085);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .security-text {{
            color: white;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .holographic-effect {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, 
                transparent 30%, 
                rgba(255, 255, 255, 0.1) 50%, 
                transparent 70%);
            pointer-events: none;
            animation: shimmer 3s infinite;
        }}

        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}

        .corner-accent {{
            position: absolute;
            width: 30px;
            height: 30px;
            background: rgba(255, 255, 255, 0.2);
        }}

        .corner-accent.top-left {{
            top: 0;
            left: 0;
            border-bottom-right-radius: 100%;
        }}

        .corner-accent.bottom-right {{
            bottom: 40px;
            right: 0;
            border-top-left-radius: 100%;
        }}

        .qr-image {{
            width: 120px;
            height: 120px;
            border-radius: 8px;
        }}

        .serial-number {{
            font-size: 10px;
            opacity: 0.8;
            font-family: monospace;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="badge-container">
        <div class="badge">
            <div class="corner-accent top-left"></div>
            <div class="corner-accent bottom-right"></div>
            <div class="holographic-effect"></div>
            
            <div class="badge-header">
                <div class="company-logo">PL</div>
                <div class="company-name">PL PROJECT</div>
                <div class="company-tagline">Revolution in Edge Dyeing Machines</div>
            </div>

            <div class="employee-section">
                <div class="employee-photo">
                    <img src="data:image/png;base64,{qr_base64}" alt="Access QR Code" class="qr-image">
                </div>
                <div class="employee-name">{user.get_full_name()}</div>
                <div class="employee-position">{user.role.value}</div>
                <div class="employee-id">ID: {str(user.id).zfill(3)}</div>
                
                <div class="access-level">
                    <div class="access-item">Machine</div>
                    <div class="access-item">Production</div>
                    <div class="access-item">Safety</div>
                </div>

                <div class="serial-number">Serial: {serial_number}</div>
            </div>

            <div class="security-strip">
                <div class="security-text">Valid Until: {expiration_date.strftime('%m/%Y')} • Authorized Personnel Only</div>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    # Create output directory and save HTML
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    html_filename = f"{user.get_full_name().replace(' ', '_')}_{user.id}_printable_card.html"
    html_path = os.path.join(output_dir, html_filename)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Printable HTML card created: {html_path}")
    return html_path


def send_complete_access_package_email(
    user: User,
    pkpass_path: str,
    google_pay_path: str,
    html_card_path: str
) -> bool:
    """
    Send complete access package via email including all formats.
    
    Args:
        user: User instance
        pkpass_path: Path to the .pkpass file
        google_pay_path: Path to the Google Pay JSON file
        html_card_path: Path to the printable HTML card
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        from modules.shared.shared.email.emailSender import EmailSenderService, get_professional_email_template, get_default_email_config
        
        # Get access level for email message
        access_level = DigitalPassGenerator()._get_access_level(user)
        
        template = get_professional_email_template(
            user_name=user.get_full_name(),
            message=f"""Your machine access package is ready! This email contains:

📱 <strong>Digital Wallet Passes:</strong>
• iPhone/Apple Wallet: Open the .pkpass attachment
• Android/Google Pay: Use the Google Pay JSON file

🖨️ <strong>Printable Card:</strong>
• Open the HTML file and print for a physical backup card

🔐 <strong>Your Access Level:</strong> {access_level}

<em>All passes contain the same QR code for machine authentication.</em>

For technical support, contact the IT department."""
        )
        
        sender = EmailSenderService(config=get_default_email_config())
        
        sender.send_email(
            subject="Your Complete Machine Access Package",
            body=template,
            to_emails=[user.email] if user.email else [],
            html=True,
            attachments=[pkpass_path, google_pay_path, html_card_path]
        )
        
        logger.info(f"Complete access package email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send complete access package email: {e}")
        return False


def main():
    """
    Demonstration of creating access passes for different user roles.
    """
    from src.frontend.pl_ui.utils.IconLoader import LOGO
    
    try:
        # Create users with different roles
        users = [
            User(
                id="001",
                firstName="Yordan",
                lastName="Zhelyazkov",
                password="temp_password",
                role=Role.ADMIN,
                email="yordan.zhelyazkov@plproject.net"
            )
        ]

        # Custom configuration with logo
        config = PassConfig(
            organization_name="PL Project LTD.",
            description="Machine Access Pass",
            logo_text="PL PROJECT",
            logo_image_path=LOGO
        )

        print("Creating access passes for multiple users...\n")
        
        for user in users:
            print(f"Creating complete access package for {user.get_full_name()} ({user.role.value})...")
            
            try:
                # Create complete package: digital passes + printable HTML card
                pkpass_path, google_pay_path, html_card_path = create_complete_access_package(
                    user=user,
                    config=config,
                    output_dir="access_passes"
                )
                
                print(f"  [OK] Digital passes created:")
                print(f"    - iPhone: {pkpass_path}")
                print(f"    - Android: {google_pay_path}")
                print(f"  [OK] Printable card: {html_card_path}")
                
                # Send complete package via email if user has email address
                if user.email:
                    success = send_complete_access_package_email(
                        user, pkpass_path, google_pay_path, html_card_path
                    )
                    if success:
                        print(f"  [EMAIL] Complete package sent to {user.email}")
                    else:
                        print(f"  [ERROR] Failed to send email to {user.email}")
                else:
                    print("  [WARNING] No email address provided - skipping email")
                    
                print()  # Empty line for readability
                
            except Exception as e:
                print(f"  [ERROR] Creating package for {user.get_full_name()}: {e}\n")

        print("[SUCCESS] All access packages processed!")
        print("\nUsage Instructions:")
        print("- iPhone users: Double-tap the .pkpass file to add to Wallet")
        print("- Android users: Use the _google_pay.json file with Google Pay")
        print("- Print backup: Open the HTML file in browser and print")
        print("- All formats contain the same QR code for machine authentication")

    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
