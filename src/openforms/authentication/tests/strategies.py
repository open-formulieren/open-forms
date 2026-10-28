from hypothesis import strategies as st

kvk_numbers = st.text(
    alphabet="0123456789",
    min_size=8,
    max_size=8,
)

branch_numbers = st.text(
    alphabet="0123456789",
    min_size=12,
    max_size=12,
)
