"""Sample Python file for compliance scanning tests."""


class ICTGovernanceFramework:
    """Board-level ICT governance framework (DORA Article 5)."""

    def assess_ict_risk(self, asset, threat_model):
        """Comprehensive ICT risk assessment (DORA Article 6)."""
        risk_tolerance = 0.8
        return self._calculate_risk(asset, threat_model, risk_tolerance)

    def _calculate_risk(self, asset, threat_model, tolerance):
        return {"risk_level": "medium", "tolerance": tolerance}


def require_mfa(user, method="totp"):
    """Multi-factor authentication (ISO 27001 A.8.5)."""
    pass


def security_log(event, user_id, resource):
    """Security event audit logging (ISO 27001 A.8.15)."""
    pass


class AnomalyDetector:
    """Automated anomaly detection (DORA Article 10)."""

    def __init__(self, baseline_model):
        self.baseline = baseline_model

    def detect(self, data):
        return {"anomalies": []}
