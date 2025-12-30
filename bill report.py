import tkinter as tk
from tkinter import messagebox

# Function to generate the bill
def generate_bill(shop_name, fertilizer_items, discount_rate, tax_rate):
    bill_text = f"========== {shop_name} ==========\n"
    bill_text += "           FERTILIZER SHOP BILL\n"
    bill_text += "=======================================\n"
    bill_text += "Item Name\tQuantity\tPrice\tTotal\n"
    bill_text += "=======================================\n"
    
    total_amount = 0
    for item in fertilizer_items:
        item_name = item['name']
        quantity = item['quantity']
        price = item['price']
        total = quantity * price
        total_amount += total
        bill_text += f"{item_name}\t{quantity}\t\t{price}\t{total}\n"
    
    # Apply discount
    discount = (discount_rate / 100) * total_amount
    discounted_amount = total_amount - discount
    
    # Apply tax
    tax = (tax_rate / 100) * discounted_amount
    final_amount = discounted_amount + tax
    
    bill_text += "=======================================\n"
    bill_text += f"Subtotal: {total_amount:.2f}\n"
    bill_text += f"Discount ({discount_rate}%): -{discount:.2f}\n"
    bill_text += f"Discounted Amount: {discounted_amount:.2f}\n"
    bill_text += f"Tax ({tax_rate}%): +{tax:.2f}\n"
    bill_text += f"Total Amount: {final_amount:.2f}\n"
    bill_text += "=======================================\n"
    bill_text += "Thank you for shopping with us!\n"
    bill_text += "=======================================\n"
    
    return bill_text

# Function to handle the "Generate Bill" button click
def on_generate_bill():
    shop_name = entry_shop_name.get()
    
    # Gather fertilizer items from the user
    fertilizer_items = []
    for i in range(len(entries_item_name)):
        item_name = entries_item_name[i].get()
        quantity = entries_quantity[i].get()
        price = entries_price[i].get()
        
        if item_name and quantity and price:
            try:
                quantity = int(quantity)
                price = float(price)
                fertilizer_items.append({"name": item_name, "quantity": quantity, "price": price})
            except ValueError:
                messagebox.showerror("Input Error", "Please enter valid quantity and price.")
                return
    
    # Get discount and tax rates
    try:
        discount_rate = float(entry_discount.get())
        tax_rate = float(entry_tax.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid discount and tax rates.")
        return
    
    # Generate the bill and display in the Text widget
    bill_text = generate_bill(shop_name, fertilizer_items, discount_rate, tax_rate)
    text_bill.delete(1.0, tk.END)
    text_bill.insert(tk.END, bill_text)

# GUI Setup
root = tk.Tk()
root.title("Fertilizer Shop Billing App")
root.geometry("600x700")

# Shop Name Entry
label_shop_name = tk.Label(root, text="Enter Shop Name:")
label_shop_name.pack()
entry_shop_name = tk.Entry(root, width=50)
entry_shop_name.pack()

# Add fertilizer items (dynamic number of items)
label_items = tk.Label(root, text="Enter Fertilizer Items (name, quantity, price):")
label_items.pack()

# Dynamic entry fields for fertilizer items
entries_item_name = []
entries_quantity = []
entries_price = []

def add_item_fields():
    item_name_label = tk.Label(root, text="Item Name:")
    item_name_label.pack()
    item_name_entry = tk.Entry(root, width=50)
    item_name_entry.pack()
    entries_item_name.append(item_name_entry)
    
    quantity_label = tk.Label(root, text="Quantity:")
    quantity_label.pack()
    quantity_entry = tk.Entry(root, width=20)
    quantity_entry.pack()
    entries_quantity.append(quantity_entry)
    
    price_label = tk.Label(root, text="Price per Unit:")
    price_label.pack()
    price_entry = tk.Entry(root, width=20)
    price_entry.pack()
    entries_price.append(price_entry)

# Button to add more items
button_add_item = tk.Button(root, text="Add Item", command=add_item_fields)
button_add_item.pack()

# Discount and Tax Entries
label_discount = tk.Label(root, text="Enter Discount Rate (%):")
label_discount.pack()
entry_discount = tk.Entry(root, width=20)
entry_discount.pack()

label_tax = tk.Label(root, text="Enter Tax Rate (%):")
label_tax.pack()
entry_tax = tk.Entry(root, width=20)
entry_tax.pack()

# Generate Bill Button
button_generate_bill = tk.Button(root, text="Generate Bill", command=on_generate_bill)
button_generate_bill.pack()

# Text Box to display the bill
text_bill = tk.Text(root, width=70, height=20)
text_bill.pack()

# Start with 1 item
add_item_fields()

# Start the application
root.mainloop()