from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets


class StudentAPISession(models.Model):
    """
    Long-lived refresh tokens (DB-backed).
    Access tokens are stateless and derived from these sessions.
    """

    student = models.ForeignKey(
        "StudentManagementSystem.Student",
        on_delete=models.CASCADE,
        related_name="api_sessions"
    )
    refresh_token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Long-lived refresh token (rotated every 7 days)."
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="Refresh token expiry (default: 7 days)."
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["student", "refresh_token"]),
            models.Index(fields=["revoked", "expires_at"]),
        ]
        verbose_name = "Student API Session"
        verbose_name_plural = "Student API Sessions"

    # ----------------------------
    # Helpers
    # ----------------------------

    def is_valid(self) -> bool:
        """Check if session is still usable."""
        return not self.revoked and self.expires_at > timezone.now()

    def mark_used(self):
        """Update last_used timestamp whenever refresh token is used."""
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])

    @classmethod
    def create_session(cls, student, lifetime_days: int = 7):
        """Issue a new refresh token (auto-revokes old ones)."""
        # 🔒 Revoke all previous sessions for security
        cls.objects.filter(student=student, revoked=False).update(revoked=True)

        token = secrets.token_urlsafe(64)  # 512-bit random
        return cls.objects.create(
            student=student,
            refresh_token=token,
            expires_at=timezone.now() + timedelta(days=lifetime_days)
        )

    @classmethod
    def rotate_session(cls, session, lifetime_days: int = 7):
        """Rotate refresh token: revoke old, issue new."""
        session.revoked = True
        session.save(update_fields=["revoked"])

        token = secrets.token_urlsafe(64)
        return cls.objects.create(
            student=session.student,
            refresh_token=token,
            expires_at=timezone.now() + timedelta(days=lifetime_days)
        )

    @classmethod
    def revoke_all(cls, student):
        """Revoke all active sessions for this student (on misuse)."""
        cls.objects.filter(student=student, revoked=False).update(revoked=True)

    def __str__(self):
        status = "Revoked" if self.revoked else "Active"
        return f"Session for {self.student} ({status}, expires {self.expires_at:%Y-%m-%d %H:%M})"
