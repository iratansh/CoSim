#!/usr/bin/env python3
"""Initialize admin user in the database."""
import asyncio
import sys
import uuid
from datetime import datetime

import asyncpg
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user():
    """Create the default admin user."""
    try:
        conn = await asyncpg.connect(
            host='postgres',
            port=5432,
            user='cosim',
            password='cosim',
            database='cosim'
        )
        
        # Generate password hash
        password_hash = pwd_context.hash('admin123')
        
        # Check if admin already exists
        existing = await conn.fetchval(
            'SELECT id FROM users WHERE email = $1',
            'admin@cosim.dev'
        )
        
        if existing:
            print('✓ Admin user already exists')
            await conn.close()
            return
        
        # Create admin user
        await conn.execute('''
            INSERT INTO users (
                id, email, hashed_password, full_name, 
                is_active, is_superuser, plan, 
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ''',
            uuid.uuid4(),
            'admin@cosim.dev',
            password_hash,
            'Admin User',
            True,
            True,
            'pro',
            datetime.utcnow(),
            datetime.utcnow()
        )
        
        print('✓ Admin user created successfully')
        print('  Email: admin@cosim.dev')
        print('  Password: admin123')
        
        await conn.close()
        
    except Exception as e:
        print(f'✗ Error creating admin user: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(create_admin_user())
