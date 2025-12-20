"""Create initial admin user using bcrypt directly."""
import bcrypt
import uuid

# Generate a bcrypt hash for password "admin123"
password = "admin123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
hashed_str = hashed.decode('utf-8')

# Generate UUIDs
role_id = str(uuid.uuid4())
user_id = str(uuid.uuid4())

print("Run these SQL commands in your database:")
print()
print(f"""
-- Create admin role
INSERT INTO roles (id, name, description, is_system, created_at, updated_at)
VALUES ('{role_id}', 'admin', 'Administrator with full access', false, NOW(), NOW());

-- Create admin user
INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, role_id, created_at, updated_at)
VALUES ('{user_id}', 'admin@example.com', '{hashed_str}', 'Admin User', true, false, '{role_id}', NOW(), NOW());
""")

print("\nOr run this single command:")
print(f"""
docker exec $(docker ps -q -f name=postgres) psql -U universalapi -d universalapi -c "INSERT INTO roles (id, name, description, is_system, created_at, updated_at) VALUES ('{role_id}', 'admin', 'Administrator with full access', false, NOW(), NOW()); INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, role_id, created_at, updated_at) VALUES ('{user_id}', 'admin@example.com', '{hashed_str}', 'Admin User', true, false, '{role_id}', NOW(), NOW());"
""")

print("\nCredentials:")
print(f"Email: admin@example.com")
print(f"Password: {password}")
