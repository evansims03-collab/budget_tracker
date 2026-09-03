# AmericasBudget
By UNEMPLOYED STUDIOS

A private, desktop-first personal finance tracker and sinking funds dashboard built with Python, Streamlit, SQLite, and Plotly.

---

## Features

- **Private & Local-First:** All data stays 100% on your computer inside a local SQLite database (`finance_tracker.db`). No cloud accounts or sensitive banking credentials required.
- **Visual Budget Health:** Central donut progress rings showing exact spend vs. budget caps, with mini-gauges for each category.
- **Sinking Funds Architecture:** Dedicated savings buckets with solvency tracking and an automatic checking reimbursement calculator.
- **One-Click Automation:** One-click monthly recurring bills (rent, utilities, insurance) and one-click monthly savings bucket contributions with duplicate-posting protection.
- **CSV Statement Importer:** Upload bank exports with customizable keyword-based auto-categorization.
- **Full Ledger Controls:** View, inline-edit, or delete both living expense transactions and past savings entries anytime.

---

## Requirements

- Python 3.9+ (or Anaconda / Miniconda)
- Git
- Google Chrome, Microsoft Edge, or any modern web browser

---

## Quickstart Guide

### 1. Clone the Repository

Open your terminal (macOS/Linux) or Command Prompt / PowerShell (Windows) and run:

```bash
git clone [https://github.com/evansims03-collab/finance-tracker.git](https://github.com/evansims03-collab/finance-tracker.git)
cd finance-tracker

```

### 2. Set Up Python & Install Dependencies
Using Conda:

```bash
conda activate base
pip install -r requirements.txt
```

Or Using Standard Python Virtual Environment (venv):
macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

3. Launch the App
Run the following command from the project folder:

```bash
streamlit run app.py
```

The app will open automatically in your browser at http://localhost:8501.

To stop the server at any time, go to your terminal and press Ctrl + C.

## One-Click Standalone Desktop Launcher (Optional)

You can launch AmericasBudget directly into its own dedicated desktop window without using the terminal:

### macOS:

1) Make the launcher script executable once in Terminal:

```bash
chmod +x AmericasBudget.command
```

2) Double-click AmericasBudget.command in Finder to launch the app directly into a standalone Chrome App window.

## Initial Setup & Customization

When you launch the app for the first time, a fresh finance_tracker.db database will automatically initialize with sample categories and sinking funds.

1) Profile / Settings Tab:

Adjust monthly targets for your living expense categories.

Adjust monthly target contributions for your savings buckets.

Configure your recurring monthly bills (rent, insurance, utilities).

Add merchant keywords (e.g., trader joe -> Groceries).

2) Add (+) Tab:

Log daily expenses or income manually.

Upload and route bank .csv statements.

Edit or delete logged transactions.

3) Savings Tab:

Click Deposit Monthly Bucket Savings to post your monthly allocations.

Track checking reimbursement amounts when spending out of savings buckets.

## Privacy Notice
Your financial transactions and database files are listed in .gitignore and are never committed to version control. Keep your local .db and exported bank CSV files private.





