from opentelemetry import metrics

meter = metrics.get_meter("openforms.submissions")

start_counter = meter.create_counter(
    "submission.starts",
    description="Amount of form submissions started (via the API).",
    unit="1",  # unitless count
)

suspension_counter = meter.create_counter(
    "submission.supensions",
    description="Amount of form submissions suspended/paused.",
    unit="1",  # unitless count
)

completion_counter = meter.create_counter(
    "submission.completions",
    unit="1",  # unitless count
    description="The number of form submissions completed by end users.",
)

step_saved_counter = meter.create_counter(
    "submission.step_saves",
    unit="1",  # unitless count
    description="The number of steps saved to the database.",
)
