"""Constants for the Bradford White Wave Client."""

# API Configuration
BASE_URL = "https://gw.prdapi.bradfordwhiteapps.com"
USER_AGENT = "Dart/3.8 (dart:io)"

# Authentication Configuration
# Azure AD B2C Settings
CLIENT_ID = "7899415d-1c23-46d8-8a79-4c15ed5f7f22"
SCOPE = ["openid", "email", "offline_access", "profile"]
REDIRECT_URI = "com.bradfordwhiteapps.bwconnect://oauth/redirect"

# B2C URLs
TENANT_DOMAIN = "consumer.bradfordwhiteapps.com"
TENANT_NAME = "consumer.bradfordwhiteapps.com" # Sometimes it's <name>.onmicrosoft.com, but URL shows this
POLICY = "B2C_1_Wave_SignIn"

AUTH_URL = f"https://{TENANT_DOMAIN}/{TENANT_NAME}/{POLICY}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://{TENANT_DOMAIN}/{TENANT_NAME}/{POLICY}/oauth2/v2.0/token"

# API Endpoints
ENDPOINT_LIST_DEVICES = "/wave/getApplianceList"
ENDPOINT_GET_STATUS = "/wave/getApplianceStatus"
ENDPOINT_GET_ENERGY = "/wave/getEnergyUsage"
ENDPOINT_SET_TEMP = "/wave/changeSetpoint"
ENDPOINT_SET_MODE = "/wave/changeOpMode"
