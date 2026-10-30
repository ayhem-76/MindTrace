
import brain_twin_db as db

test_username = "test_mindtrace_user"
test_password = "Example-Password-482!"

# Create a test account.
try:
    user_id = db.create_user(test_username, test_password)
    print("PASS: account created")
except Exception as error:
    print("Account creation failed:", error)
    raise

# Verify correct and incorrect passwords.
assert db.authenticate_user(test_username, test_password) == user_id
assert db.authenticate_user(test_username, "wrong-password") is None
print("PASS: password checks work")

# Save a sample assessment for that account.
db.save_assessment(
    user_id=user_id,
    cognitive_index=75,
    correct_count=27,
    total_questions=36,
    average_seconds=12.4,
    category_scores={
        "Logic & Patterns": 80,
        "Numerical Reasoning": 70,
    },
)

history = db.get_user_history(user_id)
assert len(history) == 1
assert history[0]["cognitive_index"] == 75
print("PASS: assessment history is saved and retrieved")

# Remove the temporary account and its test record.
db.delete_user(user_id)
assert db.get_user_history(user_id) == []
print("PASS: deleting a user removes their assessment history")

print("ALL DATABASE TESTS PASSED")
