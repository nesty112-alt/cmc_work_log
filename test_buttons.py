import sys
import tkinter as tk
from discharge_analysis import WorkLogApp

def main():
    root = tk.Tk()
    app = WorkLogApp(root)
    print("App initialized")
    
    # Try preview_html
    try:
        print("Running preview_html")
        app.preview_html()
        print("preview_html success")
    except Exception as e:
        print(f"preview_html error: {e}")
        import traceback
        traceback.print_exc()

    # Try merge_to_excel
    try:
        print("Running merge_to_excel")
        app.merge_to_excel()
        print("merge_to_excel success")
    except Exception as e:
        print(f"merge_to_excel error: {e}")
        import traceback
        traceback.print_exc()

    root.destroy()

if __name__ == "__main__":
    main()
