from django.db import models


class ShockEvent(models.Model):
    """One row per historical shock day."""

    DIRECTION_CHOICES = [('UP', 'Up'), ('DOWN', 'Down')]
    CAUSE_CHOICES = [
        ('policy', 'Policy / Regulatory'),
        ('macro', 'Macroeconomic'),
        ('geopolitical', 'Geopolitical'),
        ('technical', 'Technical / Flow'),
        ('corporate', 'Corporate Event'),
        ('unknown', 'Unknown'),
    ]

    date = models.DateField()
    index = models.CharField(max_length=20, default='NIFTY')
    open_price = models.FloatField()
    close_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    intraday_range = models.FloatField()
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    magnitude = models.FloatField()
    cause_type = models.CharField(max_length=20, choices=CAUSE_CHOICES, default='unknown')
    cause_summary = models.TextField(blank=True)
    headline = models.TextField(blank=True)
    pcr_before = models.FloatField(null=True, blank=True)
    iv_change_pct = models.FloatField(null=True, blank=True)
    fii_flow_crores = models.FloatField(null=True, blank=True)
    vix_open = models.FloatField(null=True, blank=True)
    precursor_signals = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['date', 'index'], name='unique_shock_date_index'),
        ]

    def __str__(self):
        return f"{self.date} | {self.direction} {self.magnitude:.0f}pts | {self.cause_type}"


class ShockPrecursorPattern(models.Model):
    """Aggregated fingerprint per cause_type from backtest."""

    cause_type = models.CharField(max_length=20, unique=True)
    avg_iv_change_1hr = models.FloatField(default=0)
    avg_pcr_shift = models.FloatField(default=0)
    avg_vix_open = models.FloatField(default=0)
    keyword_fingerprint = models.JSONField(default=list)
    sample_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.cause_type} pattern (n={self.sample_count})"


class ShockAlert(models.Model):
    """Fired alert during live market hours."""

    STATUS_CHOICES = [
        ('fired', 'Fired'),
        ('confirmed', 'Confirmed'),
        ('false_positive', 'False Positive'),
    ]

    fired_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()
    cause_hypothesis = models.CharField(max_length=20)
    trigger_headline = models.TextField(blank=True)
    trigger_source = models.CharField(max_length=50, blank=True)
    suggested_hedge = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='fired')
    eod_nifty_change = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-fired_at']

    def __str__(self):
        return f"{self.fired_at:%Y-%m-%d %H:%M} | score={self.score} | {self.cause_hypothesis}"
