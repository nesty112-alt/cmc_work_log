import sys
import tkinter as tk
from discharge_analysis import WorkLogApp, load_staff_list, TASK_CATEGORIES

def main():
    root = tk.Tk()
    app = WorkLogApp(root)
    
    # fake the date
    app.date_var.set("2026-07-20")
    
    # Try preview
    try:
        app.preview_html()
        print("preview OK")
    except Exception as e:
        print(f"preview exception: {repr(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
