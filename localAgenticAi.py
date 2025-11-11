import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import requests


# === DeepSeek Agent ===
class DeepSeekAgent:
    def __init__(self):
        self.model = "deepseek-coder"

    def query_ollama(self, prompt):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload)
        data = response.json()
        return data.get("response", "No response found.")

    def run(self, goal, command, log_callback):
        log_callback(f"\n🧠 Starting DeepSeek agent with goal: {goal}")
        log_callback(f"\n💻 Run Command: {command}")
        try:
            prompt = f"My goal is: {goal}. Please help me run: {command}"
            reply = self.query_ollama(prompt)
            log_callback(f"\n🤖 LLM Response:\n{reply}")
            log_callback("\n✅ Goal achieved by DeepSeek agent.")
            with open("generated_script.py", "w") as f:
                f.write(reply)
            log_callback("\n💾 Saved output to file: generated_script.py")
        except Exception as e:
            log_callback(f"\n❌ Error: {str(e)}")


# === Mistral Agent ===
class MistralAgent:
    def __init__(self):
        self.model = "mistral"

    def query_ollama(self, prompt):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload)
        data = response.json()
        return data.get("response", "No response found.")

    def run(self, goal, command, log_callback):
        log_callback(f"\n🧠 Starting Mistral agent with goal: {goal}")
        log_callback(f"\n📝 Creative Task: {command}")
        try:
            prompt = f"{goal}\n\n{command}" if command else goal
            reply = self.query_ollama(prompt)
            log_callback(f"\n🎨 LLM Response:\n{reply}")
            log_callback("\n✅ Task completed by Mistral agent.")
            with open("generated_text.txt", "w") as f:
                f.write(reply)
            log_callback("\n💾 Saved output to file: generated_text.txt")
        except Exception as e:
            log_callback(f"\n❌ Error: {str(e)}")


# === GUI ===
class AgentGUI:
    def __init__(self, root):
        self.agent = None
        root.title("Local Agentic GUI")

        tk.Label(root, text="Goal:").pack(pady=(10, 0))
        self.goal_entry = tk.Entry(root, width=60)
        self.goal_entry.pack(pady=5)

        tk.Label(root, text="Run Command (optional):").pack(pady=(10, 0))
        self.command_entry = tk.Entry(root, width=60)
        self.command_entry.pack(pady=5)

        tk.Label(root, text="Choose Model:").pack(pady=(10, 0))
        self.llm_selector = ttk.Combobox(root, values=["DeepSeek", "Mistral"])
        self.llm_selector.current(0)
        self.llm_selector.pack(pady=5)

        self.run_button = tk.Button(root, text="Run Agent", command=self.run_agent_threaded)
        self.run_button.pack(pady=10)

        self.save_button = tk.Button(root, text="Save Output to File", command=self.save_output_to_file)
        self.save_button.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, width=80, height=20)
        self.log_area.pack(pady=10)

    def log(self, message):
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)

    def run_agent_threaded(self):
        goal = self.goal_entry.get()
        command = self.command_entry.get()
        llm_backend = self.llm_selector.get()

        if llm_backend == "Mistral":
            self.agent = MistralAgent()
        else:
            self.agent = DeepSeekAgent()

        self.log(f"\n🎯 Goal: {goal}")
        self.log(f"\n💬 Command: {command}")
        self.log(f"\n⚙️ Using Model: {llm_backend}")

        threading.Thread(target=self.agent.run, args=(goal, command, self.log)).start()

    def save_output_to_file(self):
        import re
        content = self.log_area.get("1.0", tk.END)
        match = re.search(r"(🤖|🎨) LLM Response:\n(.*?)\n✅", content, re.DOTALL)
        if match:
            output_text = match.group(2).strip()
        else:
            self.log("\n⚠️ No LLM response found to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")]
        )

        if file_path:
            with open(file_path, "w") as f:
                f.write(output_text)
            self.log(f"\n💾 Saved output to: {file_path}")
        else:
            self.log("\n❌ Save cancelled.")


# === Main ===
if __name__ == "__main__":
    root = tk.Tk()
    gui = AgentGUI(root)
    root.mainloop()
