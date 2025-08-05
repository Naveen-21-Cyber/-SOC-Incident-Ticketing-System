import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3
import os
from datetime import datetime, timedelta
import csv
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

# Set matplotlib style for dark theme
plt.style.use('dark_background')

class SOCIncidentTicketing:
    def __init__(self, root):
        self.root = root
        self.root.title("SOC Incident Ticketing System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Initialize database
        self.init_database()
        
        # Apply dark theme
        self.apply_dark_theme()
        
        # Create main interface
        self.create_interface()
        
    def init_database(self):
        """Initialize SQLite database and create tables"""
        try:
            self.conn = sqlite3.connect('soc_incidents.db')
            self.cursor = self.conn.cursor()
            
            # Create incidents table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    category TEXT NOT NULL,
                    assigned_to TEXT,
                    reporter TEXT,
                    affected_system TEXT,
                    description TEXT,
                    created TEXT NOT NULL,
                    updated TEXT NOT NULL,
                    created_by TEXT,
                    resolution_notes TEXT
                )
            ''')
            
            # Create comments table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    author TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents (id)
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            
    def apply_dark_theme(self):
        """Apply dark theme to ttk widgets"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure dark theme colors
        style.configure('TLabelFrame', background='#34495e', foreground='white')
        style.configure('TLabel', background='#2c3e50', foreground='white')
        style.configure('TButton', background='#3498db', foreground='white')
        style.configure('TCombobox', fieldbackground='#34495e', foreground='white')
        style.configure('Treeview', background='#34495e', foreground='white', fieldbackground='#34495e')
        style.configure('Treeview.Heading', background='#2c3e50', foreground='white')
        
    def create_interface(self):
        """Create the main interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create PanedWindow for resizable layout
        paned_window = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg='#2c3e50', 
                                     sashwidth=5, sashrelief=tk.RAISED)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Create/Edit Incident
        left_frame = tk.Frame(paned_window, bg='#2c3e50', width=600)
        paned_window.add(left_frame, minsize=500)
        
        # Form panel
        form_panel = ttk.LabelFrame(left_frame, text="Create/Edit Incident", padding=15)
        form_panel.pack(fill=tk.X, pady=(0, 10))
        
        self.create_incident_form(form_panel)
        
        # Comments panel
        comments_panel = ttk.LabelFrame(left_frame, text="Comments & Updates", padding=15)
        comments_panel.pack(fill=tk.BOTH, expand=True)
        
        self.create_comments_section(comments_panel)
        
        # Right panel - Incident List and Statistics
        right_frame = tk.Frame(paned_window, bg='#2c3e50', width=800)
        paned_window.add(right_frame, minsize=600)
        
        # Statistics panel
        stats_panel = ttk.LabelFrame(right_frame, text="Dashboard Statistics", padding=10)
        stats_panel.pack(fill=tk.X, pady=(0, 10))
        
        self.create_statistics_panel(stats_panel)
        
        # Incident list panel
        list_panel = ttk.LabelFrame(right_frame, text="Incident List", padding=10)
        list_panel.pack(fill=tk.BOTH, expand=True)
        
        self.create_incident_list(list_panel)
        
        # Update statistics
        self.update_statistics()
        
    def create_incident_form(self, parent):
        """Create the incident creation/editing form"""
        # Create scrollable frame for form
        canvas = tk.Canvas(parent, bg='#34495e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#34495e')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields configuration
        fields = [
            ("Incident ID:", "incident_id", "entry"),
            ("Title:", "title", "entry"),
            ("Severity:", "severity", "combo"),
            ("Status:", "status", "combo"),
            ("Priority:", "priority", "combo"),
            ("Category:", "category", "combo"),
            ("Assigned To:", "assigned_to", "entry"),
            ("Reporter:", "reporter", "entry"),
            ("Affected System:", "affected_system", "entry")
        ]
        
        self.form_vars = {}
        
        for i, (label, var_name, widget_type) in enumerate(fields):
            tk.Label(scrollable_frame, text=label, bg='#34495e', fg='white', 
                    font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            
            if widget_type == "combo":
                if var_name == "severity":
                    values = ["Low", "Medium", "High", "Critical"]
                    default = "Medium"
                elif var_name == "status":
                    values = ["Open", "In Progress", "On Hold", "Resolved", "Closed"]
                    default = "Open"
                elif var_name == "priority":
                    values = ["P1 - Critical", "P2 - High", "P3 - Medium", "P4 - Low"]
                    default = "P3 - Medium"
                elif var_name == "category":
                    values = ["Malware", "Phishing", "Network Intrusion", "Data Breach", 
                             "Unauthorized Access", "DDoS", "Insider Threat", "Other"]
                    default = "Other"
                
                self.form_vars[var_name] = ttk.Combobox(scrollable_frame, values=values, 
                                                       width=30, state="readonly")
                self.form_vars[var_name].set(default)
            else:
                self.form_vars[var_name] = tk.Entry(scrollable_frame, width=33, bg='#2c3e50', 
                                                   fg='white', font=('Arial', 10), 
                                                   insertbackground='white')
            
            self.form_vars[var_name].grid(row=i, column=1, sticky='ew', pady=5)
        
        # Description field
        tk.Label(scrollable_frame, text="Description:", bg='#34495e', fg='white', 
                font=('Arial', 10, 'bold')).grid(row=len(fields), column=0, sticky='nw', 
                                                pady=5, padx=(0, 10))
        
        self.form_vars["description"] = scrolledtext.ScrolledText(scrollable_frame, width=35, height=6, 
                                                                 bg='#2c3e50', fg='white', 
                                                                 font=('Arial', 10),
                                                                 insertbackground='white')
        self.form_vars["description"].grid(row=len(fields), column=1, sticky='ew', pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(scrollable_frame, bg='#34495e')
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=15)
        
        # Create buttons
        buttons = [
            ("🆕 Create", self.create_incident, '#27ae60'),
            ("✏️ Update", self.update_incident, '#f39c12'),
            ("🗑️ Delete", self.delete_incident, '#e74c3c'),
            ("🔄 Clear", self.clear_form, '#95a5a6')
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command, bg=color, fg='white',
                          font=('Arial', 9, 'bold'), padx=8, pady=4, relief='flat',
                          activebackground=color, activeforeground='white')
            btn.pack(side=tk.LEFT, padx=3)
        
        # Configure grid weights
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def create_comments_section(self, parent):
        """Create the comments section"""
        # Comment input
        comment_input_frame = tk.Frame(parent, bg='#34495e')
        comment_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(comment_input_frame, text="Add Comment:", bg='#34495e', fg='white',
                font=('Arial', 10, 'bold')).pack(anchor='w')
        
        self.comment_text = scrolledtext.ScrolledText(comment_input_frame, height=4, bg='#2c3e50', 
                                                     fg='white', font=('Arial', 10),
                                                     insertbackground='white')
        self.comment_text.pack(fill=tk.X, pady=5)
        
        tk.Button(comment_input_frame, text="💬 Add Comment", command=self.add_comment,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'), 
                 relief='flat', pady=3).pack(pady=5)
        
        # Comments display
        tk.Label(parent, text="Comment History:", bg='#34495e', fg='white',
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10, 5))
        
        self.comments_display = scrolledtext.ScrolledText(parent, bg='#2c3e50', fg='white',
                                                         font=('Consolas', 9), state='disabled')
        self.comments_display.pack(fill=tk.BOTH, expand=True)
        
    def create_statistics_panel(self, parent):
        """Create the statistics dashboard"""
        # Create statistics frame
        self.stats_frame = tk.Frame(parent, bg='#34495e')
        self.stats_frame.pack(fill=tk.X)
        
        # Statistics variables
        self.stats_vars = {
            'total': tk.StringVar(value="0"),
            'open': tk.StringVar(value="0"),
            'critical': tk.StringVar(value="0"),
            'high': tk.StringVar(value="0"),
            'resolved_today': tk.StringVar(value="0"),
            'avg_resolution': tk.StringVar(value="0")
        }
        
        # Create stat boxes
        stats_config = [
            ("Total Incidents", self.stats_vars['total'], '#3498db'),
            ("Open Incidents", self.stats_vars['open'], '#e74c3c'),
            ("Critical Priority", self.stats_vars['critical'], '#9b59b6'),
            ("High Priority", self.stats_vars['high'], '#e67e22'),
            ("Resolved Today", self.stats_vars['resolved_today'], '#27ae60'),
            ("Avg Days to Resolve", self.stats_vars['avg_resolution'], '#34495e')
        ]
        
        for i, (label, var, color) in enumerate(stats_config):
            col = i % 3
            row = i // 3
            
            stat_frame = tk.Frame(self.stats_frame, bg=color, relief='raised', bd=2)
            stat_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            
            tk.Label(stat_frame, text=label, bg=color, fg='white', 
                    font=('Arial', 8, 'bold')).pack(pady=(3, 0))
            tk.Label(stat_frame, textvariable=var, bg=color, fg='white',
                    font=('Arial', 12, 'bold')).pack(pady=(0, 3))
        
        # Configure grid weights
        for i in range(3):
            self.stats_frame.grid_columnconfigure(i, weight=1)
        
    def create_incident_list(self, parent):
        """Create the incident list with search and filter capabilities"""
        # Search and filter frame
        search_frame = tk.Frame(parent, bg='#34495e')
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="Search:", bg='#34495e', fg='white',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_incidents)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg='#2c3e50', 
                               fg='white', font=('Arial', 10), insertbackground='white')
        search_entry.pack(side=tk.LEFT, padx=(5, 10), fill=tk.X, expand=True)
        
        tk.Label(search_frame, text="Filter:", bg='#34495e', fg='white',
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="All")
        self.filter_var.trace('w', self.filter_incidents)
        filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_var,
                                   values=["All", "Open", "Critical", "High Priority", "Resolved"],
                                   state="readonly", width=12)
        filter_combo.pack(side=tk.LEFT, padx=5)
        
        # Export and Analytics buttons
        tk.Button(search_frame, text="📊 Export CSV", command=self.export_csv,
                 bg='#16a085', fg='white', font=('Arial', 9, 'bold'), 
                 relief='flat', pady=2).pack(side=tk.RIGHT, padx=(0, 5))
        
        tk.Button(search_frame, text="📈 Analytics", command=self.open_analytics,
                 bg='#8e44ad', fg='white', font=('Arial', 9, 'bold'), 
                 relief='flat', pady=2).pack(side=tk.RIGHT)
        
        # Create frame for treeview and scrollbars
        tree_frame = tk.Frame(parent, bg='#34495e')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for incidents
        columns = ("ID", "Title", "Severity", "Status", "Priority", "Category", "Assigned", "Created", "Updated")
        self.incident_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_widths = {"ID": 120, "Title": 200, "Severity": 80, "Status": 100, 
                        "Priority": 100, "Category": 120, "Assigned": 100, "Created": 120, "Updated": 120}
        
        for col in columns:
            self.incident_tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.incident_tree.column(col, width=column_widths.get(col, 100), minwidth=50)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.incident_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.incident_tree.xview)
        
        self.incident_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for treeview and scrollbars
        self.incident_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection events
        self.incident_tree.bind('<<TreeviewSelect>>', self.on_incident_select)
        self.incident_tree.bind('<Double-1>', self.on_double_click)
        
        # Configure row colors based on severity
        self.incident_tree.tag_configure('critical', background='#e74c3c', foreground='white')
        self.incident_tree.tag_configure('high', background='#e67e22', foreground='white')
        self.incident_tree.tag_configure('medium', background='#f39c12', foreground='white')
        self.incident_tree.tag_configure('low', background='#27ae60', foreground='white')
        
        self.refresh_incident_list()
        
    def get_next_incident_number(self):
        """Get the next incident number for today"""
        today = datetime.now().strftime('%Y%m%d')
        self.cursor.execute("SELECT COUNT(*) FROM incidents WHERE id LIKE ?", (f"INC-{today}-%",))
        count = self.cursor.fetchone()[0]
        return count + 1
        
    def create_incident(self):
        """Create a new incident"""
        # Validation
        if not self.form_vars["title"].get().strip():
            messagebox.showwarning("Validation Error", "Please enter an incident title")
            return
        
        # Auto-generate ID if empty
        if not self.form_vars["incident_id"].get():
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{self.get_next_incident_number():04d}"
            self.form_vars["incident_id"].delete(0, tk.END)
            self.form_vars["incident_id"].insert(0, incident_id)
        
        incident_id = self.form_vars["incident_id"].get()
        
        # Check if incident ID already exists
        self.cursor.execute("SELECT id FROM incidents WHERE id = ?", (incident_id,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Incident ID already exists!")
            return
        
        # Insert incident into database
        try:
            self.cursor.execute('''
                INSERT INTO incidents (
                    id, title, severity, status, priority, category, assigned_to, 
                    reporter, affected_system, description, created, updated, 
                    created_by, resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                incident_id,
                self.form_vars["title"].get(),
                self.form_vars["severity"].get(),
                self.form_vars["status"].get(),
                self.form_vars["priority"].get(),
                self.form_vars["category"].get(),
                self.form_vars["assigned_to"].get(),
                self.form_vars["reporter"].get(),
                self.form_vars["affected_system"].get(),
                self.form_vars["description"].get(1.0, tk.END).strip(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.form_vars["reporter"].get() or "System",
                ""
            ))
            
            # Add creation comment
            self.cursor.execute('''
                INSERT INTO comments (incident_id, timestamp, author, comment)
                VALUES (?, ?, ?, ?)
            ''', (
                incident_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.form_vars["reporter"].get() or "System",
                f"Incident created with severity: {self.form_vars['severity'].get()}"
            ))
            
            self.conn.commit()
            self.refresh_incident_list()
            self.update_statistics()
            self.clear_form()
            
            messagebox.showinfo("Success", f"Incident {incident_id} created successfully!")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to create incident: {str(e)}")
            
    def update_incident(self):
        """Update selected incident"""
        selection = self.incident_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select an incident to update")
            return
        
        item = self.incident_tree.item(selection[0])
        incident_id = item['values'][0]
        
        # Get old values for comparison
        self.cursor.execute("SELECT status, assigned_to FROM incidents WHERE id = ?", (incident_id,))
        old_data = self.cursor.fetchone()
        if not old_data:
            messagebox.showerror("Error", "Incident not found!")
            return
        
        old_status, old_assigned = old_data
        
        try:
            # Update incident
            self.cursor.execute('''
                UPDATE incidents SET 
                    title = ?, severity = ?, status = ?, priority = ?, category = ?,
                    assigned_to = ?, reporter = ?, affected_system = ?, description = ?,
                    updated = ?
                WHERE id = ?
            ''', (
                self.form_vars["title"].get(),
                self.form_vars["severity"].get(),
                self.form_vars["status"].get(),
                self.form_vars["priority"].get(),
                self.form_vars["category"].get(),
                self.form_vars["assigned_to"].get(),
                self.form_vars["reporter"].get(),
                self.form_vars["affected_system"].get(),
                self.form_vars["description"].get(1.0, tk.END).strip(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                incident_id
            ))
            
            # Add update comment if significant changes occurred
            changes = []
            if old_status != self.form_vars["status"].get():
                changes.append(f"Status: {old_status} → {self.form_vars['status'].get()}")
            if old_assigned != self.form_vars["assigned_to"].get():
                changes.append(f"Assigned: {old_assigned} → {self.form_vars['assigned_to'].get()}")
            
            if changes:
                comment = f"Incident updated - {', '.join(changes)}"
                self.cursor.execute('''
                    INSERT INTO comments (incident_id, timestamp, author, comment)
                    VALUES (?, ?, ?, ?)
                ''', (
                    incident_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "System",
                    comment
                ))
            
            self.conn.commit()
            self.refresh_incident_list()
            self.update_statistics()
            self.refresh_comments_display()
            
            messagebox.showinfo("Success", "Incident updated successfully!")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to update incident: {str(e)}")
            
    def delete_incident(self):
        """Delete selected incident"""
        selection = self.incident_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select an incident to delete")
            return
        
        if not messagebox.askyesno("Confirm Deletion", 
                                  "Are you sure you want to delete this incident?\n\n"
                                  "This action cannot be undone and will remove all associated comments."):
            return
        
        item = self.incident_tree.item(selection[0])
        incident_id = item['values'][0]
        
        try:
            # Delete comments first (foreign key constraint)
            self.cursor.execute("DELETE FROM comments WHERE incident_id = ?", (incident_id,))
            # Delete incident
            self.cursor.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
            
            self.conn.commit()
            self.refresh_incident_list()
            self.update_statistics()
            self.clear_form()
            self.comments_display.config(state='normal')
            self.comments_display.delete(1.0, tk.END)
            self.comments_display.config(state='disabled')
            
            messagebox.showinfo("Success", "Incident deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to delete incident: {str(e)}")
            
    def clear_form(self):
        """Clear all form fields"""
        for var_name, widget in self.form_vars.items():
            if var_name in ["severity", "status", "priority", "category"]:
                defaults = {"severity": "Medium", "status": "Open", "priority": "P3 - Medium", "category": "Other"}
                widget.set(defaults[var_name])
            elif var_name == "description":
                widget.delete(1.0, tk.END)
            else:
                widget.delete(0, tk.END)
        
        # Clear comment input
        self.comment_text.delete(1.0, tk.END)
        
    def add_comment(self):
        """Add comment to selected incident"""
        selection = self.incident_tree.selection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select an incident to add a comment")
            return
        
        comment_content = self.comment_text.get(1.0, tk.END).strip()
        if not comment_content:
            messagebox.showwarning("Validation Error", "Please enter a comment")
            return
        
        item = self.incident_tree.item(selection[0])
        incident_id = item['values'][0]
        
        try:
            # Add comment
            self.cursor.execute('''
                INSERT INTO comments (incident_id, timestamp, author, comment)
                VALUES (?, ?, ?, ?)
            ''', (
                incident_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Analyst",  # In a real system, this would be the logged-in user
                comment_content
            ))
            
            # Update incident's last updated time
            self.cursor.execute('''
                UPDATE incidents SET updated = ? WHERE id = ?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), incident_id))
            
            self.conn.commit()
            self.refresh_incident_list()
            self.refresh_comments_display()
            self.comment_text.delete(1.0, tk.END)
            
            messagebox.showinfo("Success", "Comment added successfully!")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to add comment: {str(e)}")
            
    def on_incident_select(self, event):
        """Handle incident selection"""
        selection = self.incident_tree.selection()
        if selection:
            item = self.incident_tree.item(selection[0])
            incident_id = item['values'][0]
            
            # Get incident data from database
            self.cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            incident = self.cursor.fetchone()
            
            if incident:
                # Clear and populate form
                self.form_vars["incident_id"].delete(0, tk.END)
                self.form_vars["incident_id"].insert(0, incident[0])
                self.form_vars["title"].delete(0, tk.END)
                self.form_vars["title"].insert(0, incident[1])
                self.form_vars["severity"].set(incident[2])
                self.form_vars["status"].set(incident[3])
                self.form_vars["priority"].set(incident[4])
                self.form_vars["category"].set(incident[5])
                self.form_vars["assigned_to"].delete(0, tk.END)
                self.form_vars["assigned_to"].insert(0, incident[6] or "")
                self.form_vars["reporter"].delete(0, tk.END)
                self.form_vars["reporter"].insert(0, incident[7] or "")
                self.form_vars["affected_system"].delete(0, tk.END)
                self.form_vars["affected_system"].insert(0, incident[8] or "")
                self.form_vars["description"].delete(1.0, tk.END)
                self.form_vars["description"].insert(1.0, incident[9] or "")
            
            # Refresh comments display
            self.refresh_comments_display()
            
    def on_double_click(self, event):
        """Handle double-click on incident"""
        selection = self.incident_tree.selection()
        if selection:
            item = self.incident_tree.item(selection[0])
            incident_id = item['values'][0]
            self.open_incident_details(incident_id)
            
    def open_incident_details(self, incident_id):
        """Open detailed view window for incident"""
        # Get incident from database
        self.cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        incident = self.cursor.fetchone()
        
        if not incident:
            messagebox.showerror("Error", "Incident not found!")
            return
        
        # Create detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Incident Details - {incident_id}")
        detail_window.geometry("800x600")
        detail_window.configure(bg='#2c3e50')
        
        # Create notebook for tabs
        notebook = ttk.Notebook(detail_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Details tab
        details_frame = ttk.Frame(notebook)
        notebook.add(details_frame, text="📋 Details")
        
        # Create details display
        details_text = scrolledtext.ScrolledText(details_frame, bg='#34495e', fg='white',
                                                font=('Consolas', 10), state='disabled')
        details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Populate details
        details_content = f"""
INCIDENT DETAILS
{'='*50}
ID: {incident[0]}
Title: {incident[1]}
Severity: {incident[2]}
Status: {incident[3]}
Priority: {incident[4]}
Category: {incident[5]}
Assigned To: {incident[6] or 'Unassigned'}
Reporter: {incident[7] or 'Unknown'}
Affected System: {incident[8] or 'Not specified'}
Created: {incident[10]}
Updated: {incident[11]}
Created By: {incident[12] or 'System'}

DESCRIPTION:
{'-'*50}
{incident[9] or 'No description provided.'}

RESOLUTION NOTES:
{'-'*50}
{incident[13] or 'No resolution notes available.'}
"""
        
        details_text.config(state='normal')
        details_text.insert(1.0, details_content)
        details_text.config(state='disabled')
        
        # Comments tab
        comments_frame = ttk.Frame(notebook)
        notebook.add(comments_frame, text="💬 Comments")
        
        comments_text = scrolledtext.ScrolledText(comments_frame, bg='#34495e', fg='white',
                                                 font=('Consolas', 10), state='disabled')
        comments_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get and populate comments
        self.cursor.execute('''
            SELECT timestamp, author, comment FROM comments 
            WHERE incident_id = ? ORDER BY timestamp ASC
        ''', (incident_id,))
        comments = self.cursor.fetchall()
        
        if comments:
            comments_content = ""
            for comment in comments:
                comments_content += f"""
[{comment[0]}] {comment[1]}:
{comment[2]}
{'-'*60}
"""
        else:
            comments_content = "No comments available."
        
        comments_text.config(state='normal')
        comments_text.insert(1.0, comments_content)
        comments_text.config(state='disabled')
        
    def refresh_comments_display(self):
        """Refresh the comments display for selected incident"""
        selection = self.incident_tree.selection()
        if not selection:
            return
        
        item = self.incident_tree.item(selection[0])
        incident_id = item['values'][0]
        
        self.comments_display.config(state='normal')
        self.comments_display.delete(1.0, tk.END)
        
        # Get comments from database
        self.cursor.execute('''
            SELECT timestamp, author, comment FROM comments 
            WHERE incident_id = ? ORDER BY timestamp ASC
        ''', (incident_id,))
        comments = self.cursor.fetchall()
        
        if comments:
            for comment in comments:
                self.comments_display.insert(tk.END, f"[{comment[0]}] {comment[1]}:\n")
                self.comments_display.insert(tk.END, f"{comment[2]}\n")
                self.comments_display.insert(tk.END, "-" * 60 + "\n\n")
        else:
            self.comments_display.insert(tk.END, "No comments for this incident.")
        
        self.comments_display.config(state='disabled')
        self.comments_display.see(tk.END)
        
    def refresh_incident_list(self):
        """Refresh the incident list"""
        # Clear existing items
        for item in self.incident_tree.get_children():
            self.incident_tree.delete(item)
        
        # Get incidents from database
        self.cursor.execute('''
            SELECT id, title, severity, status, priority, category, 
                   assigned_to, created, updated 
            FROM incidents ORDER BY created DESC
        ''')
        incidents = self.cursor.fetchall()
        
        # Add incidents to tree
        for incident in incidents:
            # Determine row tag based on severity
            tag = incident[2].lower()
            
            self.incident_tree.insert('', tk.END, values=(
                incident[0],
                incident[1][:40] + '...' if len(incident[1]) > 40 else incident[1],
                incident[2],
                incident[3],
                incident[4],
                incident[5],
                incident[6] or 'Unassigned',
                incident[7][:16] if incident[7] else '',
                incident[8][:16] if incident[8] else ''
            ), tags=(tag,))
        
        # Apply current filter
        self.filter_incidents()
        
    def filter_incidents(self, *args):
        """Filter incidents based on search and filter criteria"""
        search_term = self.search_var.get().lower()
        filter_value = self.filter_var.get()
        
        # Clear current display
        for item in self.incident_tree.get_children():
            self.incident_tree.delete(item)
        
        # Build query based on filters
        query = '''
            SELECT id, title, severity, status, priority, category, 
                   assigned_to, created, updated 
            FROM incidents WHERE 1=1
        '''
        params = []
        
        if search_term:
            query += " AND (LOWER(title) LIKE ? OR LOWER(id) LIKE ?)"
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        if filter_value != "All":
            if filter_value == "Open":
                query += " AND status IN ('Open', 'In Progress')"
            elif filter_value == "Critical":
                query += " AND severity = 'Critical'"
            elif filter_value == "High Priority":
                query += " AND priority LIKE 'P1%'"
            elif filter_value == "Resolved":
                query += " AND status IN ('Resolved', 'Closed')"
        
        query += " ORDER BY created DESC"
        
        # Execute query and populate tree
        self.cursor.execute(query, params)
        incidents = self.cursor.fetchall()
        
        for incident in incidents:
            tag = incident[2].lower()
            self.incident_tree.insert('', tk.END, values=(
                incident[0],
                incident[1][:40] + '...' if len(incident[1]) > 40 else incident[1],
                incident[2],
                incident[3],
                incident[4],
                incident[5],
                incident[6] or 'Unassigned',
                incident[7][:16] if incident[7] else '',
                incident[8][:16] if incident[8] else ''
            ), tags=(tag,))
    
    def sort_column(self, col):
        """Sort incidents by column"""
        # Get current items
        items = [(self.incident_tree.set(item, col), item) for item in self.incident_tree.get_children('')]
        
        # Sort items
        items.sort()
        
        # Rearrange items
        for index, (val, item) in enumerate(items):
            self.incident_tree.move(item, '', index)
    
    def update_statistics(self):
        """Update dashboard statistics"""
        try:
            # Get total incidents
            self.cursor.execute("SELECT COUNT(*) FROM incidents")
            total = self.cursor.fetchone()[0]
            
            # Get open incidents
            self.cursor.execute("SELECT COUNT(*) FROM incidents WHERE status IN ('Open', 'In Progress')")
            open_incidents = self.cursor.fetchone()[0]
            
            # Get critical incidents
            self.cursor.execute("SELECT COUNT(*) FROM incidents WHERE severity = 'Critical'")
            critical = self.cursor.fetchone()[0]
            
            # Get high priority incidents
            self.cursor.execute("SELECT COUNT(*) FROM incidents WHERE priority LIKE 'P1%'")
            high_priority = self.cursor.fetchone()[0]
            
            # Get resolved today
            today = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("""
                SELECT COUNT(*) FROM incidents 
                WHERE status IN ('Resolved', 'Closed') 
                AND DATE(updated) = ?
            """, (today,))
            resolved_today = self.cursor.fetchone()[0]
            
            # Calculate average resolution time
            self.cursor.execute("""
                SELECT AVG(
                    JULIANDAY(updated) - JULIANDAY(created)
                ) as avg_days
                FROM incidents 
                WHERE status IN ('Resolved', 'Closed')
            """)
            avg_result = self.cursor.fetchone()[0]
            avg_resolution = avg_result if avg_result else 0
            
            # Update statistics
            self.stats_vars['total'].set(str(total))
            self.stats_vars['open'].set(str(open_incidents))
            self.stats_vars['critical'].set(str(critical))
            self.stats_vars['high'].set(str(high_priority))
            self.stats_vars['resolved_today'].set(str(resolved_today))
            self.stats_vars['avg_resolution'].set(f"{avg_resolution:.1f}")
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
            for var in self.stats_vars.values():
                var.set("0")
    
    def export_csv(self):
        """Export incidents to CSV file"""
        # Check if there are incidents
        self.cursor.execute("SELECT COUNT(*) FROM incidents")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showwarning("Export Error", "No incidents to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Incidents",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'title', 'severity', 'status', 'priority', 'category',
                                 'assigned_to', 'reporter', 'affected_system', 'description',
                                 'created', 'updated', 'created_by', 'resolution_notes']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    
                    # Get all incidents
                    self.cursor.execute("SELECT * FROM incidents")
                    incidents = self.cursor.fetchall()
                    
                    for incident in incidents:
                        writer.writerow({
                            'id': incident[0],
                            'title': incident[1],
                            'severity': incident[2],
                            'status': incident[3],
                            'priority': incident[4],
                            'category': incident[5],
                            'assigned_to': incident[6] or '',
                            'reporter': incident[7] or '',
                            'affected_system': incident[8] or '',
                            'description': incident[9] or '',
                            'created': incident[10],
                            'updated': incident[11],
                            'created_by': incident[12] or '',
                            'resolution_notes': incident[13] or ''
                        })
                
                # Also export comments if any exist
                comments_filename = filename.replace('.csv', '_comments.csv')
                with open(comments_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['incident_id', 'timestamp', 'author', 'comment'])
                    
                    self.cursor.execute("SELECT incident_id, timestamp, author, comment FROM comments")
                    comments = self.cursor.fetchall()
                    
                    for comment in comments:
                        writer.writerow([comment[0], comment[1], comment[2], comment[3]])
                
                messagebox.showinfo("Export Success", 
                                   f"Incidents exported to:\n{filename}\n\nComments exported to:\n{comments_filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    def open_analytics(self):
        """Open analytics dashboard window"""
        analytics_window = tk.Toplevel(self.root)
        analytics_window.title("SOC Analytics Dashboard")
        analytics_window.geometry("1200x800")
        analytics_window.configure(bg='#2c3e50')
        
        # Create notebook for different analytics tabs
        notebook = ttk.Notebook(analytics_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Overview tab
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="📊 Overview")
        self.create_overview_plots(overview_frame)
        
        # Trends tab
        trends_frame = ttk.Frame(notebook)
        notebook.add(trends_frame, text="📈 Trends")
        self.create_trends_plots(trends_frame)
        
    def create_overview_plots(self, parent):
        """Create overview plots"""
        # Create main frame
        canvas_frame = tk.Frame(parent, bg='#2c3e50')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create figure with subplots
        fig = Figure(figsize=(12, 8), facecolor='#2c3e50')
        
        # Get data for plots
        self.cursor.execute("""
            SELECT severity, COUNT(*) FROM incidents 
            GROUP BY severity
        """)
        severity_data = dict(self.cursor.fetchall())
        
        self.cursor.execute("""
            SELECT status, COUNT(*) FROM incidents 
            GROUP BY status
        """)
        status_data = dict(self.cursor.fetchall())
        
        self.cursor.execute("""
            SELECT category, COUNT(*) FROM incidents 
            GROUP BY category
        """)
        category_data = dict(self.cursor.fetchall())
        
        # Severity Distribution (Pie Chart)
        ax1 = fig.add_subplot(2, 2, 1)
        if severity_data:
            colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
            wedges, texts, autotexts = ax1.pie(
                severity_data.values(), 
                labels=severity_data.keys(),
                autopct='%1.1f%%',
                colors=colors,
                textprops={'color': 'white', 'fontsize': 10}
            )
            ax1.set_title('Incidents by Severity', color='white', fontsize=12, pad=20)
        
        # Status Distribution (Bar Chart)
        ax2 = fig.add_subplot(2, 2, 2)
        if status_data:
            bars = ax2.bar(status_data.keys(), status_data.values(), 
                          color=['#3498db', '#e67e22', '#95a5a6', '#27ae60', '#e74c3c'])
            ax2.set_title('Incidents by Status', color='white', fontsize=12, pad=20)
            ax2.set_ylabel('Count', color='white')
            ax2.tick_params(colors='white')
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', color='white')
        
        # Category Distribution (Horizontal Bar Chart)
        ax3 = fig.add_subplot(2, 2, 3)
        if category_data:
            y_pos = np.arange(len(category_data))
            colors_list = plt.cm.Set3(np.linspace(0, 1, len(category_data)))
            bars = ax3.barh(y_pos, list(category_data.values()), color=colors_list)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(list(category_data.keys()))
            ax3.set_title('Incidents by Category', color='white', fontsize=12, pad=20)
            ax3.set_xlabel('Count', color='white')
            ax3.tick_params(colors='white')
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, category_data.values())):
                ax3.text(value + 0.1, bar.get_y() + bar.get_height()/2.,
                        f'{value}', ha='left', va='center', color='white')
        
        # Recent Activity
        ax4 = fig.add_subplot(2, 2, 4)
        self.cursor.execute("""
            SELECT DATE(created) as date, COUNT(*) as count
            FROM incidents 
            WHERE created >= date('now', '-7 days')
            GROUP BY DATE(created)
            ORDER BY date
        """)
        recent_data = self.cursor.fetchall()
        
        if recent_data:
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in recent_data]
            counts = [row[1] for row in recent_data]
            
            ax4.plot(dates, counts, marker='o', linewidth=2, markersize=6, 
                    color='#3498db', markerfacecolor='#e74c3c')
            ax4.fill_between(dates, counts, alpha=0.3, color='#3498db')
            ax4.set_title('Incidents (Last 7 Days)', color='white', fontsize=12)
            ax4.set_ylabel('Count', color='white')
            ax4.tick_params(colors='white')
            ax4.xaxis.set_major_formatter(DateFormatter('%m-%d'))
            plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Create canvas and add to frame
        canvas = FigureCanvasTkAgg(fig, canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add refresh button
        refresh_btn = tk.Button(canvas_frame, text="🔄 Refresh Charts", 
                               command=lambda: self.refresh_overview_plots(fig, canvas),
                               bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        refresh_btn.pack(pady=10)
    
    def create_trends_plots(self, parent):
        """Create trend analysis plots"""
        canvas_frame = tk.Frame(parent, bg='#2c3e50')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        fig = Figure(figsize=(12, 8), facecolor='#2c3e50')
        
        # Get incidents created per day for the last 30 days
        self.cursor.execute("""
            SELECT DATE(created) as date, COUNT(*) as count
            FROM incidents 
            WHERE created >= date('now', '-30 days')
            GROUP BY DATE(created)
            ORDER BY date
        """)
        daily_incidents = self.cursor.fetchall()
        
        # Get resolution time trends
        self.cursor.execute("""
            SELECT DATE(created) as date, 
                   AVG(JULIANDAY(updated) - JULIANDAY(created)) as avg_resolution_time
            FROM incidents 
            WHERE status IN ('Resolved', 'Closed')
            AND created >= date('now', '-30 days')
            GROUP BY DATE(created)
            ORDER BY date
        """)
        resolution_trends = self.cursor.fetchall()
        
        # Incidents per day trend
        ax1 = fig.add_subplot(2, 2, 1)
        if daily_incidents:
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in daily_incidents]
            counts = [row[1] for row in daily_incidents]
            
            ax1.plot(dates, counts, marker='o', linewidth=2, markersize=6, 
                    color='#3498db', markerfacecolor='#e74c3c')
            ax1.fill_between(dates, counts, alpha=0.3, color='#3498db')
            ax1.set_title('Daily Incident Creation (Last 30 Days)', color='white', fontsize=12)
            ax1.set_ylabel('Number of Incidents', color='white')
            ax1.tick_params(colors='white')
            ax1.xaxis.set_major_formatter(DateFormatter('%m-%d'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            ax1.grid(True, alpha=0.3)
        
        # Resolution time trend
        ax2 = fig.add_subplot(2, 2, 2)
        if resolution_trends:
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in resolution_trends]
            times = [row[1] for row in resolution_trends]
            
            ax2.plot(dates, times, marker='s', linewidth=2, markersize=6, 
                    color='#27ae60', markerfacecolor='#f39c12')
            ax2.set_title('Average Resolution Time Trend', color='white', fontsize=12)
            ax2.set_ylabel('Days to Resolve', color='white')
            ax2.tick_params(colors='white')
            ax2.xaxis.set_major_formatter(DateFormatter('%m-%d'))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            ax2.grid(True, alpha=0.3)
        
        # Monthly comparison by severity
        ax3 = fig.add_subplot(2, 1, 2)
        self.cursor.execute("""
            SELECT strftime('%Y-%m', created) as month, 
                   severity,
                   COUNT(*) as count
            FROM incidents
            WHERE created >= date('now', '-6 months')
            GROUP BY month, severity
            ORDER BY month
        """)
        monthly_data = self.cursor.fetchall()
        
        if monthly_data:
            # Organize data for stacked bar chart
            months = sorted(list(set([row[0] for row in monthly_data])))
            severities = ['Low', 'Medium', 'High', 'Critical']
            data_dict = {sev: [] for sev in severities}
            
            for month in months:
                month_data = {sev: 0 for sev in severities}
                for row in monthly_data:
                    if row[0] == month:
                        month_data[row[1]] = row[2]
                for sev in severities:
                    data_dict[sev].append(month_data[sev])
            
            # Create stacked bar chart
            bottom = np.zeros(len(months))
            colors = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
            
            for i, (sev, color) in enumerate(zip(severities, colors)):
                ax3.bar(months, data_dict[sev], bottom=bottom, 
                       label=sev, color=color, alpha=0.8)
                bottom += np.array(data_dict[sev])
            
            ax3.set_title('Monthly Incidents by Severity', color='white', fontsize=12)
            ax3.set_ylabel('Number of Incidents', color='white')
            ax3.tick_params(colors='white')
            ax3.legend(facecolor='#34495e', edgecolor='white', labelcolor='white')
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        refresh_btn = tk.Button(canvas_frame, text="🔄 Refresh Trends", 
                               command=lambda: self.refresh_trends_plots(fig, canvas),
                               bg='#27ae60', fg='white', font=('Arial', 10, 'bold'))
        refresh_btn.pack(pady=10)
    
    def refresh_overview_plots(self, fig, canvas):
        """Refresh overview plots with current data"""
        fig.clear()
        self.create_overview_plots(canvas.get_tk_widget().master)
        canvas.draw()
    
    def refresh_trends_plots(self, fig, canvas):
        """Refresh trends plots with current data"""
        fig.clear()
        self.create_trends_plots(canvas.get_tk_widget().master)
        canvas.draw()
    
    def __del__(self):
        """Cleanup database connection"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass

def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    # Set application properties
    root.configure(bg='#2c3e50')
    root.minsize(1200, 800)
    
    # Create the application
    app = SOCIncidentTicketing(root)
    
    # Center the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (1400 // 2)
    y = (root.winfo_screenheight() // 2) - (900 // 2)
    root.geometry(f'1400x900+{x}+{y}')
    
    # Handle window closing
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            try:
                app.conn.close()
            except:
                pass
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()