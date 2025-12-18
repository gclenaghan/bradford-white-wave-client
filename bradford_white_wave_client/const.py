"""Constants for the Bradford White Wave Client."""

# API Configuration
BASE_URL = "https://gw.prdapi.bradfordwhiteapps.com"
USER_AGENT = "Dart/3.8 (dart:io)"

# Authentication Configuration
# Azure AD B2C Settings
CLIENT_ID = "7899415d-1c23-46d8-8a79-4c15ed5f7f22"
SCOPE = ["openid", "email", "offline_access", "profile"]
REDIRECT_URI = "com.bradfordwhiteapps.bwconnect://oauth/redirect"

# TODO: The exact B2C Authorize URL was not provided.
# Typical format: https://<tenant>.b2clogin.com/<tenant>.onmicrosoft.com/<policy>/oauth2/v2.0/authorize
# We need to find the Tenant and Policy.
AUTH_URL = None 

# API Endpoints
ENDPOINT_LIST_DEVICES = "/wave/getApplianceList"
ENDPOINT_GET_STATUS = "/wave/getApplianceStatus"
ENDPOINT_GET_ENERGY = "/wave/getEnergyUsage"
ENDPOINT_SET_TEMP = "/wave/changeSetpoint"
ENDPOINT_SET_MODE = "/wave/changeOpMode"
