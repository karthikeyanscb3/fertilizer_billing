import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import sqlite3
import os

class FertilizerBillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌱 Fertilizer Shop Billing System")
        self.root.geometry("1300x850")
        self.root.configure(bg="#1a1a2e")
        
        # Initialize database
        self.init_database()
        
        # Variables
        self.cart_items = []
        self.invoice_number = self.generate_invoice_number()
        self.calculated_values = {
            'subtotal': 0, 'discount_rate': 0, 'discount_amount': 0,
            'tax_rate': 18, 'tax_amount': 0, 'total': 0
        }
        
        # Colors
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'danger': '#f44336',
            'warning': '#ff9800',
            'dark': '#1a1a2e',
            'light': '#eaeaea',
            'card': '#16213e',
            'text': '#ffffff',
            'success': '#00c853',
            'purple': '#9c27b0'
        }
        
        # Create UI
        self.create_header()
        self.create_main_content()
        self.create_footer()
        
        # Load inventory
        self.load_inventory()
        
        # Shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_bill())
        self.root.bind('<Control-s>', lambda e: self.save_bill_to_db())
        self.root.bind('<F5>', lambda e: self.load_inventory())
        # editing state for bills
        self.editing_bill_id = None
    
    def init_database(self):
        """Initialize SQLite database"""
        self.conn = sqlite3.connect('fertilizer_shop.db')
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                category TEXT,
                unit TEXT DEFAULT 'kg',
                description TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                address TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                subtotal REAL,
                discount_rate REAL,
                discount_amount REAL,
                tax_rate REAL,
                tax_amount REAL,
                total_amount REAL,
                payment_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER,
                item_name TEXT,
                quantity INTEGER,
                price REAL,
                total REAL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                shop_name TEXT DEFAULT 'Fertilizer Shop',
                shop_address TEXT,
                shop_phone TEXT,
                default_tax REAL DEFAULT 18.0,
                currency TEXT DEFAULT 'Rs.',
                gst_number TEXT DEFAULT '',
                licence_number TEXT DEFAULT ''
            )
        ''')
        
        # Insert default settings
        self.cursor.execute('SELECT COUNT(*) FROM settings')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO settings (id, shop_name, shop_address, shop_phone, default_tax, currency, gst_number, licence_number)
                VALUES (1, 'Green Valley Fertilizers', '123 Farm Road, City', '+91 9876543210', 18.0, 'Rs.', '', '')
            ''')

        # Ensure settings table has gst_number and licence_number columns (migrate older DBs)
        try:
            self.cursor.execute("PRAGMA table_info('settings')")
            scols = [row[1] for row in self.cursor.fetchall()]
            if 'gst_number' not in scols:
                try:
                    self.cursor.execute("ALTER TABLE settings ADD COLUMN gst_number TEXT DEFAULT ''")
                except sqlite3.OperationalError:
                    pass
            if 'licence_number' not in scols:
                try:
                    self.cursor.execute("ALTER TABLE settings ADD COLUMN licence_number TEXT DEFAULT ''")
                except sqlite3.OperationalError:
                    pass
        except Exception:
            pass

        # Ensure inventory table has 'description' column (migrate older DBs)
        try:
            self.cursor.execute("PRAGMA table_info('inventory')")
            cols = [row[1] for row in self.cursor.fetchall()]
            if 'description' not in cols:
                try:
                    self.cursor.execute("ALTER TABLE inventory ADD COLUMN description TEXT")
                except sqlite3.OperationalError:
                    # If ALTER fails for any reason, ignore - insertion will fail later with clear error
                    pass
        except Exception:
            # If PRAGMA fails (e.g., table doesn't exist yet), ignore and proceed
            pass
        
        # Insert sample inventory if empty
        self.cursor.execute('SELECT COUNT(*) FROM inventory')
        if self.cursor.fetchone()[0] == 0:
            sample_items = [
                ('Urea (46-0-0)', 350.00, 100, 'Nitrogen', 'kg', 'High nitrogen fertilizer'),
                ('DAP (18-46-0)', 1350.00, 80, 'Phosphorus', 'kg', 'Diammonium phosphate'),
                ('MOP (0-0-60)', 850.00, 60, 'Potassium', 'kg', 'Muriate of potash'),
                ('NPK 10-26-26', 1200.00, 50, 'Complex', 'kg', 'Complex fertilizer'),
                ('SSP (0-16-0)', 400.00, 70, 'Phosphorus', 'kg', 'Single super phosphate'),
                ('Zinc Sulphate', 120.00, 40, 'Micronutrient', 'kg', 'Zinc supplement'),
                ('Organic Compost', 200.00, 200, 'Organic', 'kg', 'Natural compost'),
                ('Vermicompost', 15.00, 150, 'Organic', 'kg', 'Worm compost'),
                ('Neem Cake', 25.00, 100, 'Organic', 'kg', 'Natural pesticide'),
                ('Calcium Nitrate', 65.00, 45, 'Calcium', 'kg', 'Calcium supplement'),
            ]
            self.cursor.executemany('''
                INSERT INTO inventory (name, price, stock, category, unit, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', sample_items)
        
        self.conn.commit()
    
    def generate_invoice_number(self):
        date_str = datetime.now().strftime("%Y%m%d")
        self.cursor.execute('SELECT COUNT(*) FROM bills WHERE DATE(created_at) = DATE("now")')
        count = self.cursor.fetchone()[0] + 1
        return f"INV-{date_str}-{count:04d}"
    
    def create_header(self):
        header_frame = tk.Frame(self.root, bg=self.colors['dark'], pady=10)
        header_frame.pack(fill='x')
        
        self.cursor.execute('SELECT shop_name FROM settings WHERE id=1')
        settings = self.cursor.fetchone()
        shop_name = settings[0] if settings else "Fertilizer Shop"
        
        # Title
        title_frame = tk.Frame(header_frame, bg=self.colors['dark'])
        title_frame.pack(fill='x')
        
        title_label = tk.Label(title_frame, 
                              text=f"🌱 {shop_name}",
                              font=('Helvetica', 26, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['dark'])
        title_label.pack(side='left', padx=20)
        
        # Quick Action Buttons in Header
        btn_frame = tk.Frame(title_frame, bg=self.colors['dark'])
        btn_frame.pack(side='right', padx=20)
        
        # ADD FERTILIZER BUTTON
        add_fert_btn = tk.Button(btn_frame, text="+ ADD FERTILIZER",
                                command=self.show_add_fertilizer_window,
                                bg=self.colors['success'], fg='white',
                                font=('Helvetica', 11, 'bold'),
                                cursor='hand2', padx=15, pady=8)
        add_fert_btn.pack(side='left', padx=5)
        
        # Edit Prices Button
        edit_price_btn = tk.Button(btn_frame, text="EDIT PRICES",
                                  command=self.show_edit_prices_window,
                                  bg=self.colors['warning'], fg='white',
                                  font=('Helvetica', 11, 'bold'),
                                  cursor='hand2', padx=15, pady=8)
        edit_price_btn.pack(side='left', padx=5)
        
        # View Inventory Button
        inventory_btn = tk.Button(btn_frame, text="INVENTORY",
                                 command=self.show_inventory_window,
                                 bg=self.colors['secondary'], fg='white',
                                 font=('Helvetica', 11, 'bold'),
                                 cursor='hand2', padx=15, pady=8)
        inventory_btn.pack(side='left', padx=5)
        
        # Sales Report Button
        report_btn = tk.Button(btn_frame, text="REPORTS",
                              command=self.show_sales_report,
                              bg=self.colors['purple'], fg='white',
                              font=('Helvetica', 11, 'bold'),
                              cursor='hand2', padx=15, pady=8)
        report_btn.pack(side='left', padx=5)
        
        # Settings Button
        settings_btn = tk.Button(btn_frame, text="SETTINGS",
                                command=self.show_settings,
                                bg=self.colors['card'], fg='white',
                                font=('Helvetica', 10),
                                cursor='hand2', padx=10, pady=8)
        settings_btn.pack(side='left', padx=5)
        
        # Info bar
        info_frame = tk.Frame(header_frame, bg=self.colors['dark'])
        info_frame.pack(fill='x', padx=20, pady=5)
        
        self.date_label = tk.Label(info_frame,
                                   text=f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
                                   font=('Helvetica', 11),
                                   fg=self.colors['light'],
                                   bg=self.colors['dark'])
        self.date_label.pack(side='left')
        
        self.invoice_label = tk.Label(info_frame,
                                      text=f"Invoice: {self.invoice_number}",
                                      font=('Helvetica', 11, 'bold'),
                                      fg=self.colors['warning'],
                                      bg=self.colors['dark'])
        self.invoice_label.pack(side='right')
    
    def create_main_content(self):
        main_frame = tk.Frame(self.root, bg=self.colors['dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left panel
        left_panel = tk.Frame(main_frame, bg=self.colors['card'], relief='raised', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.create_customer_section(left_panel)
        self.create_item_selection(left_panel)
        self.create_cart_section(left_panel)
        
        # Right panel
        right_panel = tk.Frame(main_frame, bg=self.colors['card'], relief='raised', bd=2)
        right_panel.pack(side='right', fill='both', expand=True)
        
        self.create_bill_preview(right_panel)
    
    def create_customer_section(self, parent):
        customer_frame = tk.LabelFrame(parent, text=" Customer Information ",
                                       font=('Helvetica', 11, 'bold'),
                                       fg=self.colors['primary'],
                                       bg=self.colors['card'],
                                       pady=8, padx=8)
        customer_frame.pack(fill='x', padx=10, pady=8)
        
        row1 = tk.Frame(customer_frame, bg=self.colors['card'])
        row1.pack(fill='x', pady=3)
        
        tk.Label(row1, text="Name:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        self.customer_name = tk.Entry(row1, font=('Helvetica', 10), width=18)
        self.customer_name.pack(side='left', padx=(5, 15))
        
        tk.Label(row1, text="Phone:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        self.customer_phone = tk.Entry(row1, font=('Helvetica', 10), width=12)
        self.customer_phone.pack(side='left', padx=(5, 5))
        
        search_btn = tk.Button(row1, text="Search", command=self.search_customer,
                              bg=self.colors['secondary'], fg='white',
                              font=('Helvetica', 9), cursor='hand2')
        search_btn.pack(side='left', padx=5)
        
        tk.Label(row1, text="Address:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=(10, 0))
        self.customer_address = tk.Entry(row1, font=('Helvetica', 10), width=25)
        self.customer_address.pack(side='left', padx=(5, 0))
    
    def create_item_selection(self, parent):
        item_frame = tk.LabelFrame(parent, text=" Add Items to Cart ",
                                  font=('Helvetica', 11, 'bold'),
                                  fg=self.colors['primary'],
                                  bg=self.colors['card'],
                                  pady=8, padx=8)
        item_frame.pack(fill='x', padx=10, pady=8)
        
        # Row 1 - Select from inventory
        row1 = tk.Frame(item_frame, bg=self.colors['card'])
        row1.pack(fill='x', pady=5)
        
        tk.Label(row1, text="Select Fertilizer:", font=('Helvetica', 10, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        
        self.item_var = tk.StringVar()
        self.item_combo = ttk.Combobox(row1, textvariable=self.item_var,
                                       font=('Helvetica', 10), width=28, state='readonly')
        self.item_combo.pack(side='left', padx=10)
        self.item_combo.bind('<<ComboboxSelected>>', self.on_item_selected)
        
        tk.Label(row1, text="Price:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        self.price_var = tk.StringVar(value="Rs. 0.00")
        tk.Label(row1, textvariable=self.price_var,
                font=('Helvetica', 11, 'bold'),
                fg=self.colors['success'], bg=self.colors['card']).pack(side='left', padx=5)
        
        tk.Label(row1, text="Stock:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=(10, 0))
        self.stock_var = tk.StringVar(value="0")
        tk.Label(row1, textvariable=self.stock_var,
                font=('Helvetica', 11, 'bold'),
                fg=self.colors['warning'], bg=self.colors['card']).pack(side='left', padx=5)
        
        # Row 2 - Quantity and Add button
        row2 = tk.Frame(item_frame, bg=self.colors['card'])
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text="Quantity:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        
        self.quantity_var = tk.StringVar(value="1")
        quantity_frame = tk.Frame(row2, bg=self.colors['card'])
        quantity_frame.pack(side='left', padx=10)
        
        minus_btn = tk.Button(quantity_frame, text=" - ", 
                             command=lambda: self.change_quantity(-1),
                             bg=self.colors['danger'], fg='white',
                             font=('Helvetica', 10, 'bold'), width=3)
        minus_btn.pack(side='left')
        
        quantity_entry = tk.Entry(quantity_frame, textvariable=self.quantity_var,
                                 font=('Helvetica', 12, 'bold'), width=6, justify='center')
        quantity_entry.pack(side='left', padx=5)
        
        plus_btn = tk.Button(quantity_frame, text=" + ",
                            command=lambda: self.change_quantity(1),
                            bg=self.colors['success'], fg='white',
                            font=('Helvetica', 10, 'bold'), width=3)
        plus_btn.pack(side='left')
        
        add_btn = tk.Button(row2, text=" ADD TO CART ", command=self.add_to_cart,
                           bg=self.colors['primary'], fg='white',
                           font=('Helvetica', 11, 'bold'), cursor='hand2',
                           padx=25, pady=5)
        add_btn.pack(side='left', padx=20)
        
        # Quick Add New Fertilizer Button
        quick_add_btn = tk.Button(row2, text="New Fertilizer",
                                 command=self.show_add_fertilizer_window,
                                 bg=self.colors['purple'], fg='white',
                                 font=('Helvetica', 10), cursor='hand2',
                                 padx=10, pady=5)
        quick_add_btn.pack(side='right', padx=5)
        
        # Row 3 - Custom item entry
        row3 = tk.Frame(item_frame, bg=self.colors['card'])
        row3.pack(fill='x', pady=5)
        
        tk.Label(row3, text="Or Quick Add:", font=('Helvetica', 10),
                fg=self.colors['warning'], bg=self.colors['card']).pack(side='left')
        
        self.custom_item = tk.Entry(row3, font=('Helvetica', 10), width=18)
        self.custom_item.pack(side='left', padx=5)
        self.custom_item.insert(0, "Item Name")
        self.custom_item.bind('<FocusIn>', lambda e: self.clear_placeholder(self.custom_item, "Item Name"))
        self.custom_item.bind('<FocusOut>', lambda e: self.restore_placeholder(self.custom_item, "Item Name"))
        
        self.custom_price = tk.Entry(row3, font=('Helvetica', 10), width=10)
        self.custom_price.pack(side='left', padx=5)
        self.custom_price.insert(0, "Price")
        self.custom_price.bind('<FocusIn>', lambda e: self.clear_placeholder(self.custom_price, "Price"))
        self.custom_price.bind('<FocusOut>', lambda e: self.restore_placeholder(self.custom_price, "Price"))
        
        self.custom_qty = tk.Entry(row3, font=('Helvetica', 10), width=6)
        self.custom_qty.pack(side='left', padx=5)
        self.custom_qty.insert(0, "Qty")
        self.custom_qty.bind('<FocusIn>', lambda e: self.clear_placeholder(self.custom_qty, "Qty"))
        self.custom_qty.bind('<FocusOut>', lambda e: self.restore_placeholder(self.custom_qty, "Qty"))
        
        custom_add_btn = tk.Button(row3, text="Add Custom",
                                  command=self.add_custom_item,
                                  bg=self.colors['secondary'], fg='white',
                                  font=('Helvetica', 9), cursor='hand2')
        custom_add_btn.pack(side='left', padx=10)
    
    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
    
    def restore_placeholder(self, entry, placeholder):
        if entry.get() == "":
            entry.insert(0, placeholder)
    
    def create_cart_section(self, parent):
        cart_frame = tk.LabelFrame(parent, text=" Shopping Cart ",
                                  font=('Helvetica', 11, 'bold'),
                                  fg=self.colors['primary'],
                                  bg=self.colors['card'],
                                  pady=8, padx=8)
        cart_frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Treeview
        columns = ('Item', 'Qty', 'Price', 'Total')
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show='headings', height=8)
        
        self.cart_tree.heading('Item', text='Item Name')
        self.cart_tree.heading('Qty', text='Qty')
        self.cart_tree.heading('Price', text='Price')
        self.cart_tree.heading('Total', text='Total')
        
        # FIXED: Changed 'right' to 'e' (east)
        self.cart_tree.column('Item', width=220)
        self.cart_tree.column('Qty', width=60, anchor='center')
        self.cart_tree.column('Price', width=80, anchor='e')
        self.cart_tree.column('Total', width=100, anchor='e')
        
        scrollbar = ttk.Scrollbar(cart_frame, orient='vertical', command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=scrollbar.set)
        
        self.cart_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Cart buttons
        btn_frame = tk.Frame(cart_frame, bg=self.colors['card'])
        btn_frame.pack(fill='x', pady=8)
        
        remove_btn = tk.Button(btn_frame, text="Remove Selected",
                              command=self.remove_from_cart,
                              bg=self.colors['danger'], fg='white',
                              font=('Helvetica', 9), cursor='hand2')
        remove_btn.pack(side='left', padx=5)
        
        clear_btn = tk.Button(btn_frame, text="Clear All",
                             command=self.clear_cart,
                             bg=self.colors['warning'], fg='white',
                             font=('Helvetica', 9), cursor='hand2')
        clear_btn.pack(side='left', padx=5)
        
        # Cart summary
        self.cart_count_label = tk.Label(btn_frame, text="Items: 0",
                                        font=('Helvetica', 10, 'bold'),
                                        fg=self.colors['light'],
                                        bg=self.colors['card'])
        self.cart_count_label.pack(side='right', padx=10)
    
    def create_bill_preview(self, parent):
        preview_frame = tk.LabelFrame(parent, text=" Bill Preview ",
                                     font=('Helvetica', 11, 'bold'),
                                     fg=self.colors['primary'],
                                     bg=self.colors['card'],
                                     pady=8, padx=8)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Bill text area
        self.bill_text = tk.Text(preview_frame, font=('Courier', 10),
                                bg='white', fg='black', height=14, width=48)
        self.bill_text.pack(fill='both', expand=True, pady=5)
        
        # Calculation section
        calc_frame = tk.Frame(preview_frame, bg=self.colors['card'])
        calc_frame.pack(fill='x', pady=8)
        
        # Row 1: Discount and Tax
        row1 = tk.Frame(calc_frame, bg=self.colors['card'])
        row1.pack(fill='x', pady=3)
        
        tk.Label(row1, text="Discount %:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=5)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = tk.Entry(row1, textvariable=self.discount_var,
                                 font=('Helvetica', 10), width=6)
        discount_entry.pack(side='left', padx=5)
        discount_entry.bind('<KeyRelease>', lambda e: self.update_bill_preview())
        
        tk.Label(row1, text="Tax (GST) %:", font=('Helvetica', 10),
            fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=(20, 5))
        self.tax_var = tk.StringVar(value="0")
        self.tax_combobox = ttk.Combobox(row1, textvariable=self.tax_var, font=('Helvetica', 10), width=6,
                         values=["0", "5", "12", "18", "28"])
        self.tax_combobox.pack(side='left', padx=5)
        self.tax_combobox.set(self.tax_var.get())
        self.tax_combobox.bind('<<ComboboxSelected>>', lambda e: self.update_bill_preview())
        self.tax_combobox.bind('<KeyRelease>', lambda e: self.update_bill_preview())
        
        # Row 2: Payment method
        row2 = tk.Frame(calc_frame, bg=self.colors['card'])
        row2.pack(fill='x', pady=3)
        
        tk.Label(row2, text="Payment Mode:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=5)
        self.payment_var = tk.StringVar(value="Cash")
        
        for method in ['Cash', 'Card', 'UPI', 'Credit']:
            rb = tk.Radiobutton(row2, text=method, variable=self.payment_var,
                               value=method, bg=self.colors['card'],
                               fg=self.colors['light'], selectcolor=self.colors['dark'],
                               font=('Helvetica', 9))
            rb.pack(side='left', padx=5)
        
        # Total display
        total_frame = tk.Frame(preview_frame, bg=self.colors['success'], pady=12)
        total_frame.pack(fill='x', pady=8)
        
        self.total_label = tk.Label(total_frame, text="TOTAL: Rs. 0.00",
                                   font=('Helvetica', 22, 'bold'),
                                   fg='white',
                                   bg=self.colors['success'])
        self.total_label.pack()
        
        # Action buttons
        action_frame = tk.Frame(preview_frame, bg=self.colors['card'])
        action_frame.pack(fill='x', pady=8)
        
        new_btn = tk.Button(action_frame, text="NEW BILL",
                           command=self.new_bill,
                           bg=self.colors['secondary'], fg='white',
                           font=('Helvetica', 11, 'bold'), cursor='hand2',
                           padx=15, pady=8)
        new_btn.pack(side='left', padx=5)
        
        generate_btn = tk.Button(action_frame, text="GENERATE",
                                command=self.generate_bill,
                                bg=self.colors['primary'], fg='white',
                                font=('Helvetica', 11, 'bold'), cursor='hand2',
                                padx=15, pady=8)
        generate_btn.pack(side='left', padx=5, fill='x', expand=True)
        
        save_btn = tk.Button(action_frame, text="SAVE & PRINT",
                            command=self.save_and_print,
                            bg=self.colors['warning'], fg='white',
                            font=('Helvetica', 11, 'bold'), cursor='hand2',
                            padx=15, pady=8)
        save_btn.pack(side='right', padx=5)
    
    def create_footer(self):
        footer_frame = tk.Frame(self.root, bg=self.colors['dark'], pady=8)
        footer_frame.pack(fill='x', side='bottom')
        
        self.cursor.execute('SELECT COUNT(*) FROM bills WHERE DATE(created_at) = DATE("now")')
        today_bills = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE DATE(created_at) = DATE("now")')
        today_sales = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM inventory')
        total_items = self.cursor.fetchone()[0]
        
        stats_label = tk.Label(footer_frame, 
                              text=f"Today: {today_bills} Bills | Sales: Rs.{today_sales:.2f} | Inventory: {total_items} items",
                              font=('Helvetica', 10),
                              fg=self.colors['light'],
                              bg=self.colors['dark'])
        stats_label.pack(side='left', padx=20)
        
        help_label = tk.Label(footer_frame, text="Ctrl+N: New | Ctrl+S: Save | F5: Refresh",
                             font=('Helvetica', 9),
                             fg=self.colors['light'],
                             bg=self.colors['dark'])
        help_label.pack(side='right', padx=20)
    
    # ============ ADD FERTILIZER WINDOW ============
    def show_add_fertilizer_window(self):
        """Show window to add new fertilizer with custom price"""
        window = tk.Toplevel(self.root)
        window.title("Add New Fertilizer")
        window.geometry("500x550")
        window.configure(bg=self.colors['card'])
        window.transient(self.root)
        window.grab_set()
        
        # Center window
        window.geometry("+%d+%d" % (self.root.winfo_x() + 200, self.root.winfo_y() + 100))
        
        # Title
        tk.Label(window, text="Add New Fertilizer",
                font=('Helvetica', 18, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card']).pack(pady=15)
        
        # Form frame
        form_frame = tk.Frame(window, bg=self.colors['card'])
        form_frame.pack(fill='x', padx=30, pady=10)
        
        # Fields
        fields = {}
        
        # Fertilizer Name
        tk.Label(form_frame, text="Fertilizer Name *", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        name_entry = tk.Entry(form_frame, font=('Helvetica', 12), width=35)
        name_entry.pack(fill='x', pady=2)
        name_entry.focus()
        fields['name'] = name_entry
        
        # Price
        tk.Label(form_frame, text="Price per Unit (Rs.) *", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        price_frame = tk.Frame(form_frame, bg=self.colors['card'])
        price_frame.pack(fill='x', pady=2)
        tk.Label(price_frame, text="Rs.", font=('Helvetica', 14, 'bold'),
                fg=self.colors['success'], bg=self.colors['card']).pack(side='left')
        price_entry = tk.Entry(price_frame, font=('Helvetica', 12), width=15)
        price_entry.pack(side='left', padx=5)
        fields['price'] = price_entry
        
        # Quick price buttons
        quick_price_frame = tk.Frame(form_frame, bg=self.colors['card'])
        quick_price_frame.pack(fill='x', pady=5)
        tk.Label(quick_price_frame, text="Quick Set:", font=('Helvetica', 9),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        for price in [50, 100, 200, 500, 1000, 1500]:
            btn = tk.Button(quick_price_frame, text=f"Rs.{price}",
                           command=lambda p=price: (price_entry.delete(0, tk.END), price_entry.insert(0, str(p))),
                           bg=self.colors['dark'], fg=self.colors['light'],
                           font=('Helvetica', 8))
            btn.pack(side='left', padx=2)
        
        # Stock
        tk.Label(form_frame, text="Initial Stock *", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        stock_entry = tk.Entry(form_frame, font=('Helvetica', 12), width=15)
        stock_entry.pack(anchor='w', pady=2)
        stock_entry.insert(0, "100")
        fields['stock'] = stock_entry
        
        # Category
        tk.Label(form_frame, text="Category", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        category_combo = ttk.Combobox(form_frame, font=('Helvetica', 11), width=25,
                                     values=['Nitrogen', 'Phosphorus', 'Potassium', 
                                            'Complex', 'Organic', 'Micronutrient', 'Other'])
        category_combo.pack(anchor='w', pady=2)
        category_combo.set('Other')
        fields['category'] = category_combo
        
        # Unit
        tk.Label(form_frame, text="Unit", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        unit_frame = tk.Frame(form_frame, bg=self.colors['card'])
        unit_frame.pack(anchor='w', pady=2)
        unit_var = tk.StringVar(value='kg')
        for unit in ['kg', 'g', 'L', 'mL', 'piece', 'bag']:
            rb = tk.Radiobutton(unit_frame, text=unit, variable=unit_var,
                               value=unit, bg=self.colors['card'],
                               fg=self.colors['light'], selectcolor=self.colors['dark'])
            rb.pack(side='left', padx=5)
        fields['unit'] = unit_var
        
        # Description
        tk.Label(form_frame, text="Description (Optional)", font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(anchor='w', pady=(10, 2))
        desc_entry = tk.Entry(form_frame, font=('Helvetica', 11), width=35)
        desc_entry.pack(fill='x', pady=2)
        fields['description'] = desc_entry
        
        # Buttons
        btn_frame = tk.Frame(window, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=30, pady=20)
        
        def save_fertilizer():
            try:
                name = fields['name'].get().strip()
                price = float(fields['price'].get())
                stock = int(fields['stock'].get())
                category = fields['category'].get()
                unit = fields['unit'].get()
                description = fields['description'].get()
                
                if not name:
                    messagebox.showerror("Error", "Please enter fertilizer name!")
                    return
                if price <= 0:
                    messagebox.showerror("Error", "Please enter valid price!")
                    return
                
                try:
                    self.cursor.execute('''
                        INSERT INTO inventory (name, price, stock, category, unit, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, price, stock, category, unit, description))
                    self.conn.commit()
                except sqlite3.OperationalError as oe:
                    # If column missing, try to add it and retry once
                    if 'no column named description' in str(oe).lower():
                        try:
                            self.cursor.execute("ALTER TABLE inventory ADD COLUMN description TEXT")
                            self.conn.commit()
                            self.cursor.execute('''
                                INSERT INTO inventory (name, price, stock, category, unit, description)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (name, price, stock, category, unit, description))
                            self.conn.commit()
                        except Exception:
                            raise
                    else:
                        raise
                
                self.load_inventory()
                messagebox.showinfo("Success", f"'{name}' added successfully!\nPrice: Rs.{price:.2f}")
                window.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for price and stock!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This fertilizer already exists!")
        
        def save_and_add_more():
            try:
                name = fields['name'].get().strip()
                price = float(fields['price'].get())
                stock = int(fields['stock'].get())
                category = fields['category'].get()
                unit = fields['unit'].get()
                description = fields['description'].get()
                
                if not name or price <= 0:
                    messagebox.showerror("Error", "Please fill required fields!")
                    return
                
                try:
                    self.cursor.execute('''
                        INSERT INTO inventory (name, price, stock, category, unit, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (name, price, stock, category, unit, description))
                    self.conn.commit()
                except sqlite3.OperationalError as oe:
                    if 'no column named description' in str(oe).lower():
                        try:
                            self.cursor.execute("ALTER TABLE inventory ADD COLUMN description TEXT")
                            self.conn.commit()
                            self.cursor.execute('''
                                INSERT INTO inventory (name, price, stock, category, unit, description)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (name, price, stock, category, unit, description))
                            self.conn.commit()
                        except Exception:
                            raise
                    else:
                        raise
                
                self.load_inventory()
                messagebox.showinfo("Success", f"'{name}' added! Add another...")
                
                # Clear fields for next entry
                fields['name'].delete(0, tk.END)
                fields['price'].delete(0, tk.END)
                fields['description'].delete(0, tk.END)
                fields['name'].focus()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This fertilizer already exists!")
        
        tk.Button(btn_frame, text="SAVE", command=save_fertilizer,
                 bg=self.colors['success'], fg='white',
                 font=('Helvetica', 12, 'bold'), cursor='hand2',
                 padx=25, pady=8).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="SAVE & ADD MORE", command=save_and_add_more,
                 bg=self.colors['primary'], fg='white',
                 font=('Helvetica', 12, 'bold'), cursor='hand2',
                 padx=25, pady=8).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="CANCEL", command=window.destroy,
                 bg=self.colors['danger'], fg='white',
                 font=('Helvetica', 12, 'bold'), cursor='hand2',
                 padx=25, pady=8).pack(side='right', padx=5)
    
    # ============ EDIT PRICES WINDOW ============
    def show_edit_prices_window(self):
        """Show window to edit fertilizer prices"""
        window = tk.Toplevel(self.root)
        window.title("Edit Fertilizer Prices")
        window.geometry("750x550")
        window.configure(bg=self.colors['card'])
        window.transient(self.root)
        window.grab_set()
        
        # Title
        tk.Label(window, text="Edit Fertilizer Prices",
                font=('Helvetica', 18, 'bold'),
                fg=self.colors['warning'],
                bg=self.colors['card']).pack(pady=15)
        
        # Search frame
        search_frame = tk.Frame(window, bg=self.colors['card'])
        search_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(search_frame, text="Search:", font=('Helvetica', 10),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                               font=('Helvetica', 10), width=25)
        search_entry.pack(side='left', padx=10)
        
        # Treeview
        tree_frame = tk.Frame(window, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ('ID', 'Name', 'Current Price', 'Stock', 'Category')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        tree.heading('ID', text='ID')
        tree.heading('Name', text='Fertilizer Name')
        tree.heading('Current Price', text='Current Price')
        tree.heading('Stock', text='Stock')
        tree.heading('Category', text='Category')
        
        tree.column('ID', width=40, anchor='center')
        tree.column('Name', width=220)
        tree.column('Current Price', width=120, anchor='e')
        tree.column('Stock', width=80, anchor='center')
        tree.column('Category', width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def load_items(search_term=""):
            for item in tree.get_children():
                tree.delete(item)
            
            if search_term:
                self.cursor.execute('''
                    SELECT id, name, price, stock, category FROM inventory 
                    WHERE name LIKE ? ORDER BY name
                ''', (f'%{search_term}%',))
            else:
                self.cursor.execute('SELECT id, name, price, stock, category FROM inventory ORDER BY name')
            
            for row in self.cursor.fetchall():
                tree.insert('', 'end', values=(row[0], row[1], f"Rs.{row[2]:.2f}", row[3], row[4]))
        
        load_items()
        
        search_var.trace('w', lambda *args: load_items(search_var.get()))
        
        # Edit section
        edit_frame = tk.LabelFrame(window, text=" Edit Selected Item ",
                                  font=('Helvetica', 11, 'bold'),
                                  fg=self.colors['primary'],
                                  bg=self.colors['card'])
        edit_frame.pack(fill='x', padx=20, pady=10)
        
        edit_inner = tk.Frame(edit_frame, bg=self.colors['card'])
        edit_inner.pack(fill='x', padx=10, pady=10)
        
        tk.Label(edit_inner, text="New Price (Rs.):", font=('Helvetica', 11),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left')
        new_price_entry = tk.Entry(edit_inner, font=('Helvetica', 12, 'bold'), width=12)
        new_price_entry.pack(side='left', padx=10)
        
        tk.Label(edit_inner, text="Add Stock:", font=('Helvetica', 11),
                fg=self.colors['light'], bg=self.colors['card']).pack(side='left', padx=(20, 0))
        add_stock_entry = tk.Entry(edit_inner, font=('Helvetica', 12), width=8)
        add_stock_entry.pack(side='left', padx=10)
        add_stock_entry.insert(0, "0")
        
        def on_select(event):
            selected = tree.selection()
            if selected:
                values = tree.item(selected[0])['values']
                current_price = str(values[2]).replace('Rs.', '').strip()
                new_price_entry.delete(0, tk.END)
                new_price_entry.insert(0, current_price)
        
        tree.bind('<<TreeviewSelect>>', on_select)
        
        def update_price():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a fertilizer!")
                return
            
            try:
                item_id = tree.item(selected[0])['values'][0]
                new_price = float(new_price_entry.get())
                add_stock = int(add_stock_entry.get() or 0)
                
                if new_price <= 0:
                    messagebox.showerror("Error", "Price must be greater than 0!")
                    return
                
                self.cursor.execute('''
                    UPDATE inventory SET price = ?, stock = stock + ? WHERE id = ?
                ''', (new_price, add_stock, item_id))
                self.conn.commit()
                
                load_items(search_var.get())
                self.load_inventory()
                messagebox.showinfo("Success", "Price updated successfully!")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers!")
        
        def delete_item():
            selected = tree.selection()
            if not selected:
                return
            
            item_name = tree.item(selected[0])['values'][1]
            if messagebox.askyesno("Confirm", f"Delete '{item_name}'?"):
                item_id = tree.item(selected[0])['values'][0]
                self.cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
                self.conn.commit()
                load_items(search_var.get())
                self.load_inventory()
        
        btn_frame = tk.Frame(edit_inner, bg=self.colors['card'])
        btn_frame.pack(side='right')
        
        tk.Button(btn_frame, text="UPDATE", command=update_price,
                 bg=self.colors['success'], fg='white',
                 font=('Helvetica', 10, 'bold'), padx=15).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="DELETE", command=delete_item,
                 bg=self.colors['danger'], fg='white',
                 font=('Helvetica', 10, 'bold'), padx=15).pack(side='left', padx=5)
    
    # ============ INVENTORY WINDOW ============
    def show_inventory_window(self):
        """Show full inventory management window"""
        window = tk.Toplevel(self.root)
        window.title("Inventory Management")
        window.geometry("900x600")
        window.configure(bg=self.colors['card'])
        
        # Title
        tk.Label(window, text="Inventory Management",
                font=('Helvetica', 18, 'bold'),
                fg=self.colors['secondary'],
                bg=self.colors['card']).pack(pady=15)
        
        # Buttons frame
        btn_frame = tk.Frame(window, bg=self.colors['card'])
        btn_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Button(btn_frame, text="Add Fertilizer",
                 command=self.show_add_fertilizer_window,
                 bg=self.colors['success'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Edit Prices",
                 command=self.show_edit_prices_window,
                 bg=self.colors['warning'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)

        def add_stock_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select item(s) to add stock")
                return
            qty = simpledialog.askinteger("Add Stock", "Enter quantity to add:", minvalue=1)
            if qty is None:
                return
            ids = [tree.item(s)['values'][0] for s in selected]
            for item_id in ids:
                try:
                    self.cursor.execute('UPDATE inventory SET stock = stock + ? WHERE id = ?', (qty, item_id))
                except Exception:
                    pass
            self.conn.commit()
            load_data()
            self.load_inventory()
            messagebox.showinfo("Success", f"Added {qty} units to {len(ids)} item(s)")

        def decrease_stock_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select item(s) to decrease stock")
                return
            qty = simpledialog.askinteger("Decrease Stock", "Enter quantity to decrease:", minvalue=1)
            if qty is None:
                return
            ids = [tree.item(s)['values'][0] for s in selected]
            for item_id in ids:
                try:
                    self.cursor.execute('UPDATE inventory SET stock = stock - ? WHERE id = ? AND stock >= ?', (qty, item_id, qty))
                except Exception:
                    pass
            self.conn.commit()
            load_data()
            self.load_inventory()
            messagebox.showinfo("Success", f"Decreased {qty} units from {len(ids)} item(s)")


        # Add Stock Button
        tk.Button(btn_frame, text="Add Stock",
                 command=add_stock_selected,
                 bg=self.colors['primary'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)

        # Decrease Stock Button
        tk.Button(btn_frame, text="Decrease Stock",
                 command=decrease_stock_selected,
                 bg=self.colors['danger'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)
        
        def refresh_data():
            load_data()
        
        tk.Button(btn_frame, text="Refresh",
                 command=refresh_data,
                 bg=self.colors['secondary'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)


        tk.Button(btn_frame, text="Print",
                 command=lambda: print_inventory_table(),
                 bg=self.colors['secondary'], fg='white',
                 font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)

        # Removed separate Delete Selected button (now in combined menu)

        def print_inventory_table():
            # Export current table to a temp file and print
            import tempfile
            import platform
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
            # Write header
            temp.write('ID\tName\tPrice\tStock\tCategory\tUnit\tDescription\tStatus\n')
            for row in tree.get_children():
                vals = tree.item(row)['values']
                temp.write('\t'.join(str(v) for v in vals) + '\n')
            temp.close()
            try:
                if platform.system() == 'Windows':
                    os.startfile(temp.name, 'print')
                else:
                    os.system(f'lpr "{temp.name}"')
            except Exception as e:
                messagebox.showerror("Print Error", f"Could not print: {e}")
        
        # Low stock warning
        self.cursor.execute('SELECT COUNT(*) FROM inventory WHERE stock < 20')
        low_stock_count = self.cursor.fetchone()[0]
        if low_stock_count > 0:
            tk.Label(btn_frame, text=f"Warning: {low_stock_count} items low on stock!",
                    font=('Helvetica', 10, 'bold'),
                    fg=self.colors['danger'],
                    bg=self.colors['card']).pack(side='right', padx=10)
        
        # Treeview
        tree_frame = tk.Frame(window, bg=self.colors['card'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ('ID', 'Name', 'Price', 'Stock', 'Category', 'Unit', 'Description', 'Status')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=18)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column('ID', width=40, anchor='center')
        tree.column('Name', width=220)
        tree.column('Price', width=100, anchor='e')
        tree.column('Stock', width=80, anchor='center')
        tree.column('Category', width=120)
        tree.column('Unit', width=60, anchor='center')
        tree.column('Description', width=220)
        tree.column('Status', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        def load_data():
            for item in tree.get_children():
                tree.delete(item)
            # include description if present in table
            try:
                self.cursor.execute('SELECT id, name, price, stock, category, unit, description FROM inventory ORDER BY name')
                rows = self.cursor.fetchall()
            except Exception:
                # fallback if description column missing
                self.cursor.execute('SELECT id, name, price, stock, category, unit FROM inventory ORDER BY name')
                rows = [(*r, None) for r in self.cursor.fetchall()]

            for row in rows:
                # row: id, name, price, stock, category, unit, description
                stock_val = row[3] or 0
                if stock_val >= 20:
                    status = "OK"
                elif stock_val > 0:
                    status = "Low"
                else:
                    status = "Out"
                desc = row[6] if row[6] else 'None'
                tree.insert('', 'end', values=(row[0], row[1], f"Rs.{row[2]:.2f}", row[3], row[4], row[5], desc, status))

        # add delete action for inventory window
        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select an item to delete!")
                return
            # support multiple selection
            ids = [tree.item(s)['values'][0] for s in selected]
            names = [tree.item(s)['values'][1] for s in selected]
            if messagebox.askyesno("Confirm", f"Delete {len(ids)} selected item(s)?\n" + ", ".join(names)):
                for item_id in ids:
                    try:
                        self.cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
                    except Exception:
                        pass
                self.conn.commit()
                load_data()
                self.load_inventory()
        
        load_data()
        
        # Summary
        self.cursor.execute('SELECT COUNT(*), SUM(stock), SUM(price * stock) FROM inventory')
        summary = self.cursor.fetchone()
        
        summary_frame = tk.Frame(window, bg=self.colors['dark'])
        summary_frame.pack(fill='x', pady=10)
        
        tk.Label(summary_frame, 
                text=f"Total Items: {summary[0]} | Total Stock: {summary[1] or 0} units | Inventory Value: Rs.{(summary[2] or 0):.2f}",
                font=('Helvetica', 11, 'bold'),
                fg=self.colors['light'],
                bg=self.colors['dark']).pack(pady=10)
    
    # ============ OTHER METHODS ============
    def load_inventory(self):
        self.cursor.execute('SELECT name, price, stock FROM inventory ORDER BY name')
        items = self.cursor.fetchall()
        self.inventory_data = {item[0]: {'price': item[1], 'stock': item[2]} for item in items}
        self.item_combo['values'] = list(self.inventory_data.keys())
    
    def on_item_selected(self, event):
        item_name = self.item_var.get()
        if item_name in self.inventory_data:
            self.price_var.set(f"Rs. {self.inventory_data[item_name]['price']:.2f}")
            self.stock_var.set(str(self.inventory_data[item_name]['stock']))
    
    def change_quantity(self, delta):
        try:
            current = int(self.quantity_var.get())
            new_val = max(1, current + delta)
            self.quantity_var.set(str(new_val))
        except ValueError:
            self.quantity_var.set("1")
    
    def add_to_cart(self):
        item_name = self.item_var.get()
        if not item_name:
            messagebox.showwarning("Warning", "Please select a fertilizer!")
            return
        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity!")
            return
        if quantity > self.inventory_data[item_name]['stock']:
            messagebox.showwarning("Low Stock", f"Only {self.inventory_data[item_name]['stock']} units available!")
            return
        price = self.inventory_data[item_name]['price']
        total = quantity * price
        # Remove duplicate: if item already in cart, update its quantity and total
        for idx, item in enumerate(self.cart_items):
            if item['name'] == item_name:
                # Update quantity and total
                self.cart_items[idx]['quantity'] += quantity
                self.cart_items[idx]['total'] = self.cart_items[idx]['quantity'] * price
                # Update treeview
                for row in self.cart_tree.get_children():
                    vals = self.cart_tree.item(row)['values']
                    if vals[0] == item_name:
                        new_qty = self.cart_items[idx]['quantity']
                        new_total = self.cart_items[idx]['total']
                        self.cart_tree.item(row, values=(item_name, new_qty, f"Rs.{price:.2f}", f"Rs.{new_total:.2f}"))
                        break
                self.update_bill_preview()
                self.quantity_var.set("1")
                self.cart_count_label.config(text=f"Items: {len(self.cart_items)}")
                return
        # If not in cart, add new
        self.cart_items.append({
            'name': item_name,
            'quantity': quantity,
            'price': price,
            'total': total
        })
        self.cart_tree.insert('', 'end', values=(item_name, quantity, f"Rs.{price:.2f}", f"Rs.{total:.2f}"))
        self.update_bill_preview()
        self.quantity_var.set("1")
        self.cart_count_label.config(text=f"Items: {len(self.cart_items)}")
    
    def add_custom_item(self):
        item_name = self.custom_item.get().strip()
        if item_name == "Item Name":
            item_name = ""
        try:
            price_str = self.custom_price.get()
            qty_str = self.custom_qty.get()
            if price_str == "Price" or qty_str == "Qty":
                raise ValueError
            price = float(price_str)
            quantity = int(qty_str)
        except ValueError:
            messagebox.showerror("Error", "Enter valid item name, price and quantity!")
            return
        if not item_name or price <= 0 or quantity <= 0:
            messagebox.showerror("Error", "Fill all fields correctly!")
            return
        total = quantity * price
        # Remove duplicate: if item already in cart, update its quantity and total
        for idx, item in enumerate(self.cart_items):
            if item['name'] == item_name:
                self.cart_items[idx]['quantity'] += quantity
                self.cart_items[idx]['total'] = self.cart_items[idx]['quantity'] * price
                # Update treeview
                for row in self.cart_tree.get_children():
                    vals = self.cart_tree.item(row)['values']
                    if vals[0] == item_name:
                        new_qty = self.cart_items[idx]['quantity']
                        new_total = self.cart_items[idx]['total']
                        self.cart_tree.item(row, values=(item_name, new_qty, f"Rs.{price:.2f}", f"Rs.{new_total:.2f}"))
                        break
                self.update_bill_preview()
                self.custom_item.delete(0, tk.END)
                self.custom_item.insert(0, "Item Name")
                self.custom_price.delete(0, tk.END)
                self.custom_price.insert(0, "Price")
                self.custom_qty.delete(0, tk.END)
                self.custom_qty.insert(0, "Qty")
                self.cart_count_label.config(text=f"Items: {len(self.cart_items)}")
                return
        # If not in cart, add new
        self.cart_items.append({
            'name': item_name,
            'quantity': quantity,
            'price': price,
            'total': total
        })
        self.cart_tree.insert('', 'end', values=(item_name, quantity, f"Rs.{price:.2f}", f"Rs.{total:.2f}"))
        self.update_bill_preview()
        self.custom_item.delete(0, tk.END)
        self.custom_item.insert(0, "Item Name")
        self.custom_price.delete(0, tk.END)
        self.custom_price.insert(0, "Price")
        self.custom_qty.delete(0, tk.END)
        self.custom_qty.insert(0, "Qty")
        self.cart_count_label.config(text=f"Items: {len(self.cart_items)}")
    
    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select an item to remove!")
            return
        
        for item in selected:
            index = self.cart_tree.index(item)
            self.cart_tree.delete(item)
            if index < len(self.cart_items):
                self.cart_items.pop(index)
        
        self.update_bill_preview()
        self.cart_count_label.config(text=f"Items: {len(self.cart_items)}")
    
    def clear_cart(self):
        if self.cart_items and messagebox.askyesno("Confirm", "Clear all items from cart?"):
            for item in self.cart_tree.get_children():
                self.cart_tree.delete(item)
            self.cart_items.clear()
            self.update_bill_preview()
            self.cart_count_label.config(text="Items: 0")
    
    def update_bill_preview(self):
        self.bill_text.delete(1.0, tk.END)
        
        if not self.cart_items:
            self.total_label.config(text="TOTAL: Rs. 0.00")
            return
        
        # fetch settings including gst/licence if available
        try:
            self.cursor.execute('SELECT shop_name, shop_address, shop_phone, currency, gst_number, licence_number FROM settings WHERE id=1')
            settings = self.cursor.fetchone() or ("Fertilizer Shop", "", "", "Rs.", "", "")
            shop_name = settings[0]
            shop_address = settings[1] or ""
            shop_phone = settings[2] or ""
            currency = settings[3] or "Rs."
            gst_number = settings[4] or ""
            licence_number = settings[5] or ""
        except Exception:
            # fallback if columns not present
            self.cursor.execute('SELECT shop_name, shop_address, shop_phone, currency FROM settings WHERE id=1')
            settings = self.cursor.fetchone() or ("Fertilizer Shop", "", "", "Rs.")
            shop_name = settings[0]
            shop_address = settings[1] or ""
            shop_phone = settings[2] or ""
            currency = settings[3] or "Rs."
            gst_number = ""
            licence_number = ""
        
        # Build a nicely aligned bill using fixed width font (48 chars)
        width = 48
        def center(s):
            return s.center(width)

        def wrap(s, w):
            # simple wrap that returns list of lines
            lines = []
            while len(s) > w:
                idx = s.rfind(' ', 0, w)
                if idx == -1:
                    idx = w
                lines.append(s[:idx])
                s = s[idx:].lstrip()
            if s:
                lines.append(s)
            return lines

        bill_lines = []
        bill_lines.append('=' * width)
        bill_lines.append(center(shop_name))
        if shop_address:
            for ln in wrap(shop_address, width - 6):
                bill_lines.append(ln.center(width))
        if shop_phone:
            bill_lines.append(center(f"Phone: {shop_phone}"))
        bill_lines.append('=' * width)
        # moved GST/Licence to header area (instead of showing invoice here)
        if gst_number:
            bill_lines.append(center(f"GST No: {gst_number}"))
        if licence_number:
            bill_lines.append(center(f"Licence No: {licence_number}"))
        bill_lines.append(f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        # invoice number in header
        bill_lines.append(f"Invoice: {self.invoice_number}")
        customer_name = self.customer_name.get().strip()
        if customer_name:
            bill_lines.append(f"Customer: {customer_name}")
        bill_lines.append('-' * width)
        # columns: Item(22), Qty(4), Price(9), Total(9)
        bill_lines.append(f"{'Item':<22} {'Qty':>4} {'Price':>9} {'Total':>9}")
        bill_lines.append('-' * width)

        subtotal = 0
        for item in self.cart_items:
            name = item['name'][:22]
            qty = item['quantity']
            price = item['price']
            total = item['total']
            subtotal += total
            price_str = f"{currency}{price:,.2f}"
            total_str = f"{currency}{total:,.2f}"
            line = f"{name:<22} {str(qty):>4} {price_str:>9} {total_str:>9}"
            bill_lines.append(line)

        bill_lines.append('-' * width)
        bill_lines.append(f"{'Subtotal:':<33} {currency}{subtotal:>8.2f}")

        try:
            discount_rate = float(self.discount_var.get())
        except ValueError:
            discount_rate = 0

        discount_amount = (discount_rate / 100) * subtotal
        discounted_total = subtotal - discount_amount

        if discount_rate > 0:
            bill_lines.append(f"{'Discount (' + str(discount_rate) + '%):':<33} -{currency}{discount_amount:>8.2f}")

        try:
            tax_rate = float(self.tax_var.get())
        except ValueError:
            tax_rate = 0

        tax_amount = (tax_rate / 100) * discounted_total
        final_total = discounted_total + tax_amount

        if tax_rate > 0:
            bill_lines.append(f"{'GST (' + str(tax_rate) + '%):':<33} +{currency}{tax_amount:>8.2f}")

        bill_lines.append('=' * width)
        bill_lines.append(f"{'GRAND TOTAL:':<33} {currency}{final_total:>8.2f}")
        bill_lines.append('=' * width)

        # GST/licence already shown in header; omit here to avoid duplication
        bill_lines.append(f"Payment: {self.payment_var.get()}")
        bill_lines.append("")
        bill_lines.append(center('Thank you for your purchase!'))
        bill_lines.append(center('Visit Again Soon!'))
        bill_lines.append('=' * width)

        bill = '\n'.join(bill_lines) + '\n'
        self.bill_text.insert(1.0, bill)
        self.total_label.config(text=f"TOTAL: {currency} {final_total:.2f}")
        
        self.calculated_values = {
            'subtotal': subtotal,
            'discount_rate': discount_rate,
            'discount_amount': discount_amount,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'total': final_total
        }
    
    def generate_bill(self):
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty!")
            return
        self.update_bill_preview()
        messagebox.showinfo("Success", "Bill generated successfully!")
    
    def save_bill_to_db(self):
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty!")
            return False
        
        try:
            customer_id = None
            customer_name = self.customer_name.get().strip()
            customer_phone = self.customer_phone.get().strip()
            
            if customer_phone:
                self.cursor.execute('SELECT id FROM customers WHERE phone = ?', (customer_phone,))
                result = self.cursor.fetchone()
                if result:
                    customer_id = result[0]
                else:
                    self.cursor.execute('''
                        INSERT INTO customers (name, phone, address)
                        VALUES (?, ?, ?)
                    ''', (customer_name, customer_phone, self.customer_address.get()))
                    customer_id = self.cursor.lastrowid
            # If editing an existing bill, update instead of insert
            if getattr(self, 'editing_bill_id', None):
                bill_id = self.editing_bill_id
                # restore previous stock for that bill
                self.cursor.execute('SELECT item_name, quantity FROM bill_items WHERE bill_id = ?', (bill_id,))
                for item_name, qty in self.cursor.fetchall():
                    try:
                        self.cursor.execute('UPDATE inventory SET stock = stock + ? WHERE name = ?', (qty, item_name))
                    except Exception:
                        pass
                # remove old items
                self.cursor.execute('DELETE FROM bill_items WHERE bill_id = ?', (bill_id,))

                # update bill header
                self.cursor.execute('''
                    UPDATE bills SET customer_id = ?, subtotal = ?, discount_rate = ?, discount_amount = ?,
                        tax_rate = ?, tax_amount = ?, total_amount = ?, payment_method = ?, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    customer_id,
                    self.calculated_values['subtotal'],
                    self.calculated_values['discount_rate'],
                    self.calculated_values['discount_amount'],
                    self.calculated_values['tax_rate'],
                    self.calculated_values['tax_amount'],
                    self.calculated_values['total'],
                    self.payment_var.get(),
                    bill_id
                ))

                # insert new items and deduct stock
                for item in self.cart_items:
                    self.cursor.execute('''
                        INSERT INTO bill_items (bill_id, item_name, quantity, price, total)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (bill_id, item['name'], item['quantity'], item['price'], item['total']))
                    self.cursor.execute('UPDATE inventory SET stock = stock - ? WHERE name = ?', (item['quantity'], item['name']))

                self.conn.commit()
                messagebox.showinfo("Success", f"Bill {self.invoice_number} updated!")
                # clear editing state
                self.editing_bill_id = None
                # regenerate invoice number for next new bill
                self.invoice_number = self.generate_invoice_number()
                self.invoice_label.config(text=f"Invoice: {self.invoice_number}")
                self.load_inventory()
                return True

            # Normal insert for new bill
            self.cursor.execute('''
                INSERT INTO bills (invoice_number, customer_id, subtotal, 
                                  discount_rate, discount_amount, tax_rate, 
                                  tax_amount, total_amount, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.invoice_number,
                customer_id,
                self.calculated_values['subtotal'],
                self.calculated_values['discount_rate'],
                self.calculated_values['discount_amount'],
                self.calculated_values['tax_rate'],
                self.calculated_values['tax_amount'],
                self.calculated_values['total'],
                self.payment_var.get()
            ))

            bill_id = self.cursor.lastrowid

            for item in self.cart_items:
                self.cursor.execute('''
                    INSERT INTO bill_items (bill_id, item_name, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (bill_id, item['name'], item['quantity'], item['price'], item['total']))

                self.cursor.execute('''
                    UPDATE inventory SET stock = stock - ? WHERE name = ?
                ''', (item['quantity'], item['name']))

            self.conn.commit()
            messagebox.showinfo("Success", f"Bill {self.invoice_number} saved!")
            self.load_inventory()
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            return False
    
    def save_and_print(self):
        if self.save_bill_to_db():
            self.save_as_text()
            self.new_bill()
    
    def save_as_text(self):
        if not self.cart_items:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfilename=f"Bill_{self.invoice_number}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.bill_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Bill saved to {filename}")
            try:
                os.startfile(filename)
            except:
                pass
    
    def new_bill(self):
        self.cart_items.clear()
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        self.customer_name.delete(0, tk.END)
        self.customer_phone.delete(0, tk.END)
        self.customer_address.delete(0, tk.END)
        self.discount_var.set("0")
        self.tax_var.set("18")
        self.payment_var.set("Cash")
        
        self.invoice_number = self.generate_invoice_number()
        self.invoice_label.config(text=f"Invoice: {self.invoice_number}")
        self.date_label.config(text=f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
        
        self.bill_text.delete(1.0, tk.END)
        self.total_label.config(text="TOTAL: Rs. 0.00")
        self.cart_count_label.config(text="Items: 0")
    
    def search_customer(self):
        phone = self.customer_phone.get().strip()
        if not phone:
            messagebox.showwarning("Warning", "Enter phone number to search")
            return
        
        self.cursor.execute('SELECT name, address FROM customers WHERE phone = ?', (phone,))
        result = self.cursor.fetchone()
        
        if result:
            self.customer_name.delete(0, tk.END)
            self.customer_name.insert(0, result[0] or "")
            self.customer_address.delete(0, tk.END)
            self.customer_address.insert(0, result[1] or "")
            messagebox.showinfo("Found", "Customer found!")
        else:
            messagebox.showinfo("Not Found", "Customer not in database")
    
    def show_sales_report(self):
        window = tk.Toplevel(self.root)
        window.title("Sales Report")
        window.geometry("600x500")
        window.configure(bg=self.colors['card'])
        
        tk.Label(window, text="Sales Report",
                font=('Helvetica', 18, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card']).pack(pady=15)
        
        # Statistics
        stats_frame = tk.Frame(window, bg=self.colors['card'])
        stats_frame.pack(fill='x', padx=30, pady=10)
        
        # Today
        self.cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM bills WHERE DATE(created_at) = DATE("now")
        ''')
        today = self.cursor.fetchone()
        
        # This Week
        self.cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM bills WHERE DATE(created_at) >= DATE("now", "-7 days")
        ''')
        week = self.cursor.fetchone()
        
        # This Month
        self.cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM bills WHERE strftime("%Y-%m", created_at) = strftime("%Y-%m", "now")
        ''')
        month = self.cursor.fetchone()
        
        # All Time
        self.cursor.execute('SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM bills')
        total = self.cursor.fetchone()
        
        periods = [
            ("Today", today, self.colors['success']),
            ("This Week", week, self.colors['secondary']),
            ("This Month", month, self.colors['warning']),
            ("All Time", total, self.colors['primary'])
        ]
        
        for label, (count, amount), color in periods:
            frame = tk.Frame(stats_frame, bg=self.colors['dark'], pady=15)
            frame.pack(fill='x', pady=5)
            
            tk.Label(frame, text=label, font=('Helvetica', 14, 'bold'),
                    fg=self.colors['light'], bg=self.colors['dark']).pack(side='left', padx=20)
            tk.Label(frame, text=f"{count} Bills | Rs.{amount:.2f}",
                    font=('Helvetica', 14, 'bold'),
                    fg=color, bg=self.colors['dark']).pack(side='right', padx=20)
        
        # Recent bills
        tk.Label(window, text="Recent Bills", font=('Helvetica', 12, 'bold'),
                fg=self.colors['light'], bg=self.colors['card']).pack(pady=(20, 5))
        
        columns = ('Invoice', 'Date', 'Total')
        tree = ttk.Treeview(window, columns=columns, show='headings', height=8)
        for col in columns:
            tree.heading(col, text=col)
        tree.column('Invoice', width=150)
        tree.column('Date', width=150)
        tree.column('Total', width=100, anchor='e')
        tree.pack(fill='x', padx=30, pady=5)
        
        self.cursor.execute('''
            SELECT invoice_number, created_at, total_amount FROM bills
            ORDER BY created_at DESC LIMIT 10
        ''')
        for row in self.cursor.fetchall():
            tree.insert('', 'end', values=(row[0], row[1][:16], f"Rs.{row[2]:.2f}"))

        # Actions frame for Edit/Delete
        action_frame = tk.Frame(window, bg=self.colors['card'])
        action_frame.pack(fill='x', padx=30, pady=(8, 20))

        def edit_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a bill to edit")
                return
            if len(selected) > 1:
                messagebox.showwarning("Warning", "Select only one bill to edit")
                return
            invoice = tree.item(selected[0])['values'][0]
            # load bill data
            self.cursor.execute('SELECT id, customer_id, subtotal, discount_rate, discount_amount, tax_rate, tax_amount, total_amount, payment_method, created_at FROM bills WHERE invoice_number = ?', (invoice,))
            bill = self.cursor.fetchone()
            if not bill:
                messagebox.showerror("Error", "Bill not found in database")
                return
            bill_id = bill[0]
            customer_id = bill[1]

            # load customer
            if customer_id:
                self.cursor.execute('SELECT name, phone, address FROM customers WHERE id = ?', (customer_id,))
                cust = self.cursor.fetchone()
                if cust:
                    self.customer_name.delete(0, tk.END)
                    self.customer_name.insert(0, cust[0] or '')
                    self.customer_phone.delete(0, tk.END)
                    self.customer_phone.insert(0, cust[1] or '')
                    self.customer_address.delete(0, tk.END)
                    self.customer_address.insert(0, cust[2] or '')
            else:
                self.customer_name.delete(0, tk.END)
                self.customer_phone.delete(0, tk.END)
                self.customer_address.delete(0, tk.END)

            # load bill items
            self.cart_items.clear()
            for it in self.cart_tree.get_children():
                self.cart_tree.delete(it)

            self.cursor.execute('SELECT item_name, quantity, price, total FROM bill_items WHERE bill_id = ?', (bill_id,))
            items = self.cursor.fetchall()
            for item in items:
                name, qty, price, total = item
                self.cart_items.append({'name': name, 'quantity': qty, 'price': price, 'total': total})
                self.cart_tree.insert('', 'end', values=(name, qty, f"Rs.{price:.2f}", f"Rs.{total:.2f}"))

            # load bill-level details
            self.discount_var.set(str(bill[3] or 0))
            self.tax_var.set(str(bill[5] or 0))
            self.payment_var.set(bill[8] or 'Cash')
            # set editing state
            self.editing_bill_id = bill_id
            # set invoice label to editing invoice
            self.invoice_number = invoice
            self.invoice_label.config(text=f"Invoice: {self.invoice_number} (Editing)")
            self.update_bill_preview()

        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select bill(s) to delete")
                return
            invoices = [tree.item(s)['values'][0] for s in selected]
            if not messagebox.askyesno("Confirm", f"Delete {len(invoices)} selected bill(s)?"):
                return
            for inv in invoices:
                # get bill id and items
                self.cursor.execute('SELECT id FROM bills WHERE invoice_number = ?', (inv,))
                row = self.cursor.fetchone()
                if not row:
                    continue
                bill_id = row[0]
                # restore stock from bill_items
                self.cursor.execute('SELECT item_name, quantity FROM bill_items WHERE bill_id = ?', (bill_id,))
                for item_name, qty in self.cursor.fetchall():
                    try:
                        self.cursor.execute('UPDATE inventory SET stock = stock + ? WHERE name = ?', (qty, item_name))
                    except Exception:
                        pass
                # delete bill_items and bill
                self.cursor.execute('DELETE FROM bill_items WHERE bill_id = ?', (bill_id,))
                self.cursor.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
            self.conn.commit()
            messagebox.showinfo("Deleted", "Selected bill(s) deleted")
            # refresh
            for it in tree.get_children():
                tree.delete(it)
            self.cursor.execute('''
                SELECT invoice_number, created_at, total_amount FROM bills
                ORDER BY created_at DESC LIMIT 10
            ''')
            for row in self.cursor.fetchall():
                tree.insert('', 'end', values=(row[0], row[1][:16], f"Rs.{row[2]:.2f}"))
            self.load_inventory()


        def print_sales_report_table():
            import tempfile
            import platform
            temp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
            temp.write('Invoice\tDate\tTotal\n')
            for row in tree.get_children():
                vals = tree.item(row)['values']
                temp.write('\t'.join(str(v) for v in vals) + '\n')
            temp.close()
            try:
                if platform.system() == 'Windows':
                    os.startfile(temp.name, 'print')
                else:
                    os.system(f'lpr "{temp.name}"')
            except Exception as e:
                messagebox.showerror("Print Error", f"Could not print: {e}")

        tk.Button(action_frame, text="Print", command=print_sales_report_table,
                 bg=self.colors['secondary'], fg='white', font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Edit Selected", command=edit_selected,
                 bg=self.colors['secondary'], fg='white', font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Delete Selected", command=delete_selected,
                 bg=self.colors['danger'], fg='white', font=('Helvetica', 10, 'bold')).pack(side='left', padx=5)
    
    def show_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Shop Settings")
        dialog.geometry("450x350")
        dialog.configure(bg=self.colors['card'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        self.cursor.execute('SELECT * FROM settings WHERE id=1')
        settings = self.cursor.fetchone()
        
        tk.Label(dialog, text="Shop Settings",
                font=('Helvetica', 16, 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card']).pack(pady=15)
        
        form_frame = tk.Frame(dialog, bg=self.colors['card'])
        form_frame.pack(fill='x', padx=30)
        
        fields = {}
        labels = [
            ('Shop Name:', settings[1] if settings else ''),
            ('Address:', settings[2] if settings else ''),
            ('Phone:', settings[3] if settings else ''),
            ('Default Tax %:', str(settings[4]) if settings else '18'),
            ('Currency:', settings[5] if settings else 'Rs.'),
            ('GST Number:', settings[6] if settings and len(settings) > 6 else ''),
            ('Licence Number:', settings[7] if settings and len(settings) > 7 else '')
        ]
        
        for label, value in labels:
            tk.Label(form_frame, text=label, fg=self.colors['light'],
                    bg=self.colors['card'], font=('Helvetica', 10)).pack(anchor='w', pady=2)
            entry = tk.Entry(form_frame, font=('Helvetica', 10), width=35)
            entry.insert(0, value or '')
            entry.pack(fill='x', pady=2)
            fields[label] = entry
        
        def save_settings():
            # include gst and licence in update (handle older DBs that may lack columns)
            try:
                self.cursor.execute('''
                    UPDATE settings SET 
                        shop_name = ?, shop_address = ?, shop_phone = ?,
                        default_tax = ?, currency = ?, gst_number = ?, licence_number = ?
                    WHERE id = 1
                ''', (
                    fields['Shop Name:'].get(),
                    fields['Address:'].get(),
                    fields['Phone:'].get(),
                    float(fields['Default Tax %:'].get() or 18),
                    fields['Currency:'].get() or 'Rs.',
                    fields['GST Number:'].get() if 'GST Number:' in fields else '',
                    fields['Licence Number:'].get() if 'Licence Number:' in fields else ''
                ))
            except sqlite3.OperationalError:
                # older DB without columns, try adding them then update
                try:
                    self.cursor.execute("ALTER TABLE settings ADD COLUMN gst_number TEXT DEFAULT ''")
                except Exception:
                    pass
                try:
                    self.cursor.execute("ALTER TABLE settings ADD COLUMN licence_number TEXT DEFAULT ''")
                except Exception:
                    pass
                self.cursor.execute('''
                    UPDATE settings SET 
                        shop_name = ?, shop_address = ?, shop_phone = ?,
                        default_tax = ?, currency = ?, gst_number = ?, licence_number = ?
                    WHERE id = 1
                ''', (
                    fields['Shop Name:'].get(),
                    fields['Address:'].get(),
                    fields['Phone:'].get(),
                    float(fields['Default Tax %:'].get() or 18),
                    fields['Currency:'].get() or 'Rs.',
                    fields['GST Number:'].get() if 'GST Number:' in fields else '',
                    fields['Licence Number:'].get() if 'Licence Number:' in fields else ''
                ))
            self.conn.commit()
            messagebox.showinfo("Success", "Settings saved!")
            dialog.destroy()
        
        tk.Button(dialog, text="Save Settings", command=save_settings,
                 bg=self.colors['success'], fg='white',
                 font=('Helvetica', 11, 'bold')).pack(pady=20)
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


# Run Application
if __name__ == "__main__":
    root = tk.Tk()
    app = FertilizerBillingApp(root)
    root.mainloop()