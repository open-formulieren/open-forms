from opentelemetry import metrics

meter = metrics.get_meter("openforms.submissions")

completion_counter = meter.create_counter(
    "submission.completions",
    unit="1",  # unitless count
    description="The number of form submissions completed by end users",
)
