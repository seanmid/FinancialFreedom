# Budget Tracker Application

A comprehensive web-based budgeting application that enables users to track expenses, manage payment sources, and gain financial insights.

## Features

- User authentication and access control
- Income and expense tracking
- Budget management
- Debt tracking and payoff calculator
- Financial goals tracking
- Payment source management
- Analytics and reporting
- Admin user management

## Requirements

- Python 3.11+
- PostgreSQL database
- The following Python packages:
  - streamlit
  - plotly
  - pandas
  - psycopg2-binary
  - bcrypt
  - python-dotenv

## Deployment to Streamlit.io

1. Create an account on [Streamlit.io](https://streamlit.io)

2. Connect your GitHub repository

3. Set up the following environment variables in Streamlit's dashboard:
   - `DATABASE_URL`: Your PostgreSQL database connection string
   - `SECRET_KEY`: A secure random string for session management

4. Deploy your application through Streamlit's interface

## Local Development

1. Clone the repository

2. Install dependencies:
   ```bash
   pip install streamlit plotly pandas psycopg2-binary bcrypt python-dotenv
   ```

3. Set up environment variables in a `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   SECRET_KEY=your_secret_key
   ```

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Database Setup

The application requires a PostgreSQL database. Make sure to:
1. Create a new database
2. Run the initial schema migrations
3. Set up the DATABASE_URL environment variable

## Security Notes

- Never commit `.env` files or sensitive credentials
- Use secure password hashing (already implemented with bcrypt)
- Regularly update dependencies for security patches
