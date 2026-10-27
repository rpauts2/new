#!/usr/bin/env python3
"""Small Windows-friendly desktop UI for the read-only Warframe companion."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys_path = str(Path(__file__).resolve().parent)
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

import advisor
import relic_advisor
import session_log


class CompanionApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Warframe Companion")
        self.geometry("900x650")
        self.minsize(760, 540)
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Hint.TLabel", foreground="#666666")

        ttk.Label(container, text="WARFRAME COMPANION", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="Планирование, поиск наград и личная статистика. Игрой управляет только игрок.",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(2, 12))

        tabs = ttk.Notebook(container)
        tabs.pack(fill="both", expand=True)
        self.advisor_tab = ttk.Frame(tabs, padding=12)
        self.relic_tab = ttk.Frame(tabs, padding=12)
        self.log_tab = ttk.Frame(tabs, padding=12)
        tabs.add(self.advisor_tab, text="Советник")
        tabs.add(self.relic_tab, text="Реликвии")
        tabs.add(self.log_tab, text="Журнал")
        self._build_advisor_tab()
        self._build_relic_tab()
        self._build_log_tab()

    @staticmethod
    def _text(parent: ttk.Frame, height: int = 12) -> tk.Text:
        widget = tk.Text(parent, height=height, wrap="word", font=("Consolas", 10), padx=8, pady=8)
        widget.configure(state="disabled")
        return widget

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _build_advisor_tab(self) -> None:
        form = ttk.Frame(self.advisor_tab)
        form.pack(fill="x")
        ttk.Label(form, text="Тип миссии").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.mission_var = tk.StringVar(value="Survival")
        ttk.Combobox(
            form, textvariable=self.mission_var,
            values=sorted(advisor.MISSION_ROLES, key=str.casefold), state="readonly", width=28,
        ).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Главная цель").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.goal_var = tk.StringVar(value="survive")
        ttk.Combobox(
            form, textvariable=self.goal_var,
            values=[""] + sorted(advisor.GOAL_ROLE), state="readonly", width=28,
        ).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Исключить варфреймы").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.exclude_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.exclude_var).grid(row=2, column=1, sticky="ew", pady=4)
        form.columnconfigure(1, weight=1)
        ttk.Button(form, text="Подобрать", command=self._recommend).grid(row=0, column=2, rowspan=3, padx=(12, 0), sticky="ns")

        self.advisor_output = self._text(self.advisor_tab, 18)
        self.advisor_output.pack(fill="both", expand=True, pady=(12, 0))
        self._recommend()

    def _recommend(self) -> None:
        try:
            results = advisor.recommend(
                self.mission_var.get(),
                self.goal_var.get() or None,
                8,
                tuple(self.exclude_var.get().split(",")),
            )
        except ValueError as exc:
            messagebox.showerror("Не удалось подобрать", str(exc), parent=self)
            return
        lines = [f"Подбор для миссии: {self.mission_var.get()}"]
        if self.goal_var.get():
            lines.append(f"Цель: {self.goal_var.get()}")
        lines.append("")
        if not results:
            lines.append("Нет совпадений. Убери часть исключений или выбери другую цель.")
        for index, item in enumerate(results, 1):
            roles = ", ".join(str(role).replace("_", " ") for role in item["matched_roles"])
            lines.extend([
                f"{index}. {item['frame']}  |  совпадение: {item['score']}",
                f"   Роли: {roles}",
                f"   {item['notes']}",
                "",
            ])
        lines.append("Подбор по общим ролям, не живой рейтинг меты. Проверь актуальные изменения и свою сборку.")
        self._set_text(self.advisor_output, "\n".join(lines))

    def _build_relic_tab(self) -> None:
        ttk.Label(self.relic_tab, text="JSON-набор WFCD (relics.json или all.json)").pack(anchor="w")
        path_row = ttk.Frame(self.relic_tab)
        path_row.pack(fill="x", pady=(5, 10))
        self.data_path_var = tk.StringVar(value=str(Path.home() / ".warframe_companion" / "relics.json"))
        ttk.Entry(path_row, textvariable=self.data_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(path_row, text="Выбрать…", command=self._choose_data).pack(side="left", padx=(8, 0))

        filters = ttk.Frame(self.relic_tab)
        filters.pack(fill="x")
        ttk.Label(filters, text="Награда").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.item_var = tk.StringVar(value="Forma Blueprint")
        ttk.Entry(filters, textvariable=self.item_var, width=32).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(filters, text="Эпоха").grid(row=0, column=2, sticky="w", padx=(12, 8), pady=4)
        self.tier_var = tk.StringVar()
        ttk.Combobox(filters, textvariable=self.tier_var, values=["", "Lith", "Meso", "Neo", "Axi", "Requiem"], state="readonly", width=12).grid(row=0, column=3, pady=4)
        ttk.Label(filters, text="Состояние").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.state_var = tk.StringVar()
        ttk.Combobox(filters, textvariable=self.state_var, values=["", "Intact", "Exceptional", "Flawless", "Radiant"], state="readonly", width=29).grid(row=1, column=1, sticky="ew", pady=4)
        self.exact_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="Точное название", variable=self.exact_var).grid(row=1, column=2, columnspan=2, sticky="w", padx=(12, 0), pady=4)
        filters.columnconfigure(1, weight=1)

        actions = ttk.Frame(self.relic_tab)
        actions.pack(fill="x", pady=(8, 10))
        ttk.Button(actions, text="Искать в файле", command=lambda: self._search_relics(False)).pack(side="left")
        ttk.Button(actions, text="Скачать данные и искать", command=lambda: self._search_relics(True)).pack(side="left", padx=(8, 0))
        self.relic_output = self._text(self.relic_tab, 16)
        self.relic_output.pack(fill="both", expand=True)
        ttk.Label(self.relic_tab, text="Шансы берутся из файла. Перед использованием проверь актуальность данных.", style="Hint.TLabel").pack(anchor="w", pady=(8, 0))

    def _choose_data(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Выбрать JSON данных реликвий",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if chosen:
            self.data_path_var.set(chosen)

    def _search_relics(self, download: bool) -> None:
        path = Path(self.data_path_var.get()).expanduser()
        try:
            if download:
                relic_advisor.download_dataset(path)
            relics, metadata = relic_advisor.load_dataset(path)
            results = relic_advisor.find_relics(
                relics, self.item_var.get(), tier=self.tier_var.get(),
                state=self.state_var.get(), exact=self.exact_var.get(),
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка поиска", f"{exc}\n\nЕсли файла ещё нет, нажми «Скачать данные и искать».", parent=self)
            return
        lines = [f"Файл: {path}", f"Записей реликвий: {len(relics)}"]
        if metadata:
            lines.append(f"Метаданные источника: {metadata}")
        lines.append(f"Совпадений: {len(results)}")
        lines.append("")
        if not results:
            lines.append("Награды не найдены. Проверь название и фильтры.")
        for row in results[:100]:
            chance = f"{row['chance']}%" if row["chance"] is not None else "шанс не указан"
            lines.append(f"{row['tier']} {row['relic']} | {row['state']} | {row['item']} | {chance}")
        if len(results) > 100:
            lines.append(f"\nПоказаны первые 100 из {len(results)} результатов.")
        self._set_text(self.relic_output, "\n".join(lines))

    def _build_log_tab(self) -> None:
        form = ttk.Frame(self.log_tab)
        form.pack(fill="x")
        self.log_vars = {
            "mission": tk.StringVar(value="Survival"),
            "minutes": tk.StringVar(value="5"),
            "frame": tk.StringVar(),
            "relic": tk.StringVar(),
            "reward": tk.StringVar(),
            "notes": tk.StringVar(),
        }
        fields = [
            ("Миссия", "mission"), ("Минуты", "minutes"), ("Варфрейм", "frame"),
            ("Реликвия", "relic"), ("Награда", "reward"), ("Заметка", "notes"),
        ]
        for index, (label, key) in enumerate(fields):
            row, col = divmod(index, 2)
            ttk.Label(form, text=label).grid(row=row, column=col * 2, sticky="w", padx=(0, 8), pady=5)
            ttk.Entry(form, textvariable=self.log_vars[key]).grid(row=row, column=col * 2 + 1, sticky="ew", padx=(0, 16), pady=5)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)
        buttons = ttk.Frame(self.log_tab)
        buttons.pack(fill="x", pady=(8, 10))
        ttk.Button(buttons, text="Сохранить результат", command=self._save_log).pack(side="left")
        ttk.Button(buttons, text="Обновить статистику", command=self._show_summary).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Экспорт CSV", command=self._export_csv).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Резервная копия", command=self._backup_log).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Очистить историю", command=self._clear_log).pack(side="left", padx=(8, 0))
        self.log_output = self._text(self.log_tab, 14)
        self.log_output.pack(fill="both", expand=True)
        self._show_summary()

    def _show_summary(self) -> None:
        try:
            stats = session_log.summarize(session_log.read_entries(session_log.DEFAULT_LOG))
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка журнала", str(exc), parent=self)
            return
        lines = [
            f"Файл журнала: {session_log.DEFAULT_LOG}",
            f"Сессий: {stats['sessions']} (завершено: {stats['completed_sessions']})",
            f"Время завершённых миссий: {stats['total_minutes']} мин",
            f"Средняя длительность: {stats['average_minutes']} мин",
            "",
            "По миссиям (завершённое время / средняя длительность):",
        ]
        for name, row in stats["by_mission"].items():
            lines.append(
                f"  {name}: {row['sessions']} сессий, {row['completed_minutes']} мин, "
                f"среднее {row['average_completed_minutes']} мин"
            )
        lines.extend(["", "По варфреймам (завершённое время / средняя длительность):"])
        for name, row in stats["by_frame"].items():
            lines.append(
                f"  {name}: {row['sessions']} сессий, {row['completed_minutes']} мин, "
                f"среднее {row['average_completed_minutes']} мин"
            )
        lines.extend(["", "Награды (записанные завершённые сессии):"])
        lines.extend(f"  {name}: {count}" for name, count in stats["rewards"].items())
        if not stats["rewards"]:
            lines.append("  Пока ничего не записано.")
        lines.extend(["", "Наблюдаемая частота записей (шт./час):"])
        lines.extend(f"  {name}: {rate}" for name, rate in stats["reward_rates_per_hour"].items())
        if not stats["reward_rates_per_hour"]:
            lines.append("  Недостаточно данных.")
        self._set_text(self.log_output, "\n".join(lines))

    def _save_log(self) -> None:
        try:
            minutes = float(self.log_vars["minutes"].get())
            entry = session_log.add_entry(
                session_log.DEFAULT_LOG,
                self.log_vars["mission"].get(),
                minutes,
                frame=self.log_vars["frame"].get(),
                relic=self.log_vars["relic"].get(),
                reward=self.log_vars["reward"].get(),
                notes=self.log_vars["notes"].get(),
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Не удалось сохранить", str(exc), parent=self)
            return
        messagebox.showinfo("Сохранено", f"{entry['mission']} · {entry['duration_minutes']} мин", parent=self)
        self._show_summary()

    def _export_csv(self) -> None:
        chosen = filedialog.asksaveasfilename(
            parent=self, title="Экспорт журнала", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile="warframe-missions.csv",
        )
        if not chosen:
            return
        try:
            session_log.export_csv(session_log.read_entries(session_log.DEFAULT_LOG), chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Ошибка экспорта", str(exc), parent=self)
            return
        messagebox.showinfo("Экспорт завершён", f"Файл сохранён:\n{chosen}", parent=self)

    def _backup_log(self) -> None:
        default_name = f"warframe-missions-{session_log.datetime.now(session_log.timezone.utc):%Y%m%dT%H%M%SZ}.jsonl"
        chosen = filedialog.asksaveasfilename(
            parent=self, title="Резервная копия журнала", defaultextension=".jsonl",
            filetypes=[("JSONL", "*.jsonl"), ("Все файлы", "*.*")], initialfile=default_name,
        )
        if not chosen:
            return
        try:
            backup = session_log.backup_log(session_log.DEFAULT_LOG, chosen)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Не удалось создать копию", str(exc), parent=self)
            return
        messagebox.showinfo("Резервная копия готова", f"Файл сохранён:\n{backup}", parent=self)

    def _clear_log(self) -> None:
        confirmed = messagebox.askyesno(
            "Очистить историю?",
            "Сначала будет создана резервная копия. Продолжить очистку журнала?",
            icon="warning",
            parent=self,
        )
        if not confirmed:
            return
        try:
            backup = session_log.clear_log(session_log.DEFAULT_LOG, confirm=True)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Не удалось очистить журнал", str(exc), parent=self)
            return
        messagebox.showinfo("История очищена", f"Резервная копия сохранена:\n{backup}", parent=self)
        self._show_summary()


def main() -> None:
    app = CompanionApp()
    app.mainloop()


if __name__ == "__main__":
    main()
