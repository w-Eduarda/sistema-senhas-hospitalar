from __future__ import annotations
import sys
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import DATABASE_PATH
from database.models import Consultorio, Especialidade, PerfilUsuario, Profissional, Usuario
from database.repositories import ConsultorioRepository, ConfiguracaoRepository, EspecialidadeRepository, ProfissionalRepository, UsuarioRepository
from domain.auth_service import AuthService
from services.audit_service import AuditService
from services.backup_service import BackupService
from ui.widgets import ApplicationFrame, DataTable, MessageArea

class AdminView(ApplicationFrame):
    PERFIS = tuple(item.value for item in PerfilUsuario)
    def __init__(self, master: tk.Misc, connection, **kwargs):
        super().__init__(master, "Painel administrativo", **kwargs)
        self.connection = connection
        self.specialties = EspecialidadeRepository(connection)
        self.offices = ConsultorioRepository(connection)
        self.professionals = ProfissionalRepository(connection)
        self.users = UsuarioRepository(connection)
        self.settings = ConfiguracaoRepository(connection)
        self.auth = AuthService(connection)
        self.audit = AuditService(connection)
        self.backup = BackupService(DATABASE_PATH)
        self.columnconfigure(0, weight=1); self.rowconfigure(1, weight=1)
        self.notebook = ttk.Notebook(self); self.notebook.grid(row=1, column=0, sticky="nsew")
        self._build_registry_tab(); self._build_users_tab(); self._build_settings_tab(); self._build_reports_tab(); self._build_backup_tab()
        self.message = MessageArea(self); self.message.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.refresh()

    def _build_registry_tab(self):
        tab = ttk.Frame(self.notebook, padding=10); tab.columnconfigure(0, weight=1); tab.rowconfigure(0, weight=1)
        self.notebook.add(tab, text="Cadastros")
        self.registry_book = ttk.Notebook(tab); self.registry_book.grid(row=0, column=0, sticky="nsew")
        self.specialty_table = DataTable(self.registry_book, ("id", "codigo", "nome", "tempo_medio", "ativo"))
        self.office_table = DataTable(self.registry_book, ("id", "numero", "descricao", "ativo"))
        self.professional_table = DataTable(self.registry_book, ("id", "nome", "registro", "especialidade", "consultorio", "ativo"))
        for widget, title in ((self.specialty_table, "Especialidades"), (self.office_table, "Consultórios"), (self.professional_table, "Profissionais")):
            self.registry_book.add(widget, text=title)
        actions = ttk.Frame(tab); actions.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(actions, text="Novo", command=self.create_registry_item).pack(side="left", padx=(0, 5))
        ttk.Button(actions, text="Editar selecionado", command=self.edit_registry_item).pack(side="left", padx=5)
        ttk.Button(actions, text="Ativar / desativar", command=self.toggle_registry_item).pack(side="left", padx=5)
        ttk.Button(actions, text="Atualizar", command=self.refresh).pack(side="right")

    def _build_users_tab(self):
        tab = ttk.Frame(self.notebook, padding=10); tab.columnconfigure(0, weight=1); tab.rowconfigure(0, weight=1)
        self.notebook.add(tab, text="Usuários e acessos")
        self.user_table = DataTable(tab, ("id", "login", "perfil", "ativo")); self.user_table.grid(row=0, column=0, sticky="nsew")
        actions = ttk.Frame(tab); actions.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        for text, command in (("Criar usuário", self.create_user), ("Alterar perfil", self.change_user_profile), ("Redefinir senha", self.reset_user_password), ("Ativar / desativar", self.toggle_user)):
            ttk.Button(actions, text=text, command=command).pack(side="left", padx=4)
        ttk.Button(actions, text="Atualizar", command=self.refresh).pack(side="right")
        ttk.Label(tab, text="As senhas são armazenadas como hash PBKDF2 e não são exibidas após o cadastro.", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_settings_tab(self):
        tab = ttk.Frame(self.notebook, padding=16); tab.columnconfigure(1, weight=1); self.notebook.add(tab, text="Parâmetros")
        self.setting_vars = {}
        options = (("tempo_medio_padrao", "Tempo médio padrão (minutos)", "30"), ("alternancia_normal_preferencial", "Preferenciais antes de uma normal", "3"), ("intervalo_rechamada_segundos", "Intervalo de rechamada (segundos)", "30"), ("sequencia_diaria", "Reiniciar sequência diariamente (0/1)", "1"))
        for row, (key, label, default) in enumerate(options):
            ttk.Label(tab, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
            var = tk.StringVar(value=self.settings.get(key, default) or default); self.setting_vars[key] = var
            ttk.Entry(tab, textvariable=var, width=18).grid(row=row, column=1, sticky="w", pady=6)
        ttk.Button(tab, text="Salvar parâmetros", command=self.save_settings).grid(row=len(options), column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Label(tab, text="Os parâmetros são persistidos no SQLite e usados nas operações seguintes.", style="Muted.TLabel").grid(row=len(options)+1, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _build_reports_tab(self):
        tab = ttk.Frame(self.notebook, padding=10); tab.columnconfigure(0, weight=1); tab.rowconfigure(1, weight=1); self.notebook.add(tab, text="Relatórios")
        filters = ttk.Frame(tab); filters.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filters, text="De (AAAA-MM-DD)").pack(side="left")
        self.report_start = tk.StringVar(value=date.today().replace(day=1).isoformat()); ttk.Entry(filters, textvariable=self.report_start, width=12).pack(side="left", padx=(5, 12))
        ttk.Label(filters, text="Até").pack(side="left")
        self.report_end = tk.StringVar(value=date.today().isoformat()); ttk.Entry(filters, textvariable=self.report_end, width=12).pack(side="left", padx=5)
        ttk.Button(filters, text="Gerar relatório", command=self.generate_report).pack(side="left", padx=8)
        self.report_table = DataTable(tab, ("indicador", "quantidade", "media_minutos")); self.report_table.grid(row=1, column=0, sticky="nsew")
        ttk.Label(tab, text="Médias consideram somente atendimentos finalizados; ausências e cancelamentos aparecem como contagens.", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_backup_tab(self):
        tab = ttk.Frame(self.notebook, padding=16); tab.columnconfigure(0, weight=1); tab.rowconfigure(1, weight=1); self.notebook.add(tab, text="Backup")
        ttk.Label(tab, text=f"Banco ativo: {DATABASE_PATH}", style="Muted.TLabel", wraplength=850).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.backup_table = DataTable(tab, ("arquivo", "caminho")); self.backup_table.grid(row=1, column=0, sticky="nsew")
        actions = ttk.Frame(tab); actions.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(actions, text="Criar backup", command=self.create_backup).pack(side="left")
        ttk.Button(actions, text="Restaurar backup selecionado", command=self.restore_backup).pack(side="left", padx=8)
        ttk.Button(actions, text="Atualizar", command=self.refresh_backups).pack(side="right")
        ttk.Label(tab, text="A restauração substitui o banco ativo; uma cópia de segurança é criada antes da troca.", style="Warning.TLabel").grid(row=3, column=0, sticky="w", pady=(10, 0))

    def _selected_id(self, table):
        values = table.selected_values()
        if not values:
            messagebox.showinfo("Seleção necessária", "Selecione um registro primeiro.", parent=self); return None
        return int(values[0])

    def _prompt(self, title, fields, initial=None):
        dialog = tk.Toplevel(self); dialog.title(title); dialog.transient(self.winfo_toplevel()); dialog.grab_set(); dialog.resizable(False, False)
        variables = {}
        for row, (key, label) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=6)
            var = tk.StringVar(value=(initial or {}).get(key, "")); variables[key] = var
            ttk.Entry(dialog, textvariable=var, width=38).grid(row=row, column=1, padx=12, pady=6)
        result = {"value": None}
        def accept(): result["value"] = {key: var.get().strip() for key, var in variables.items()}; dialog.destroy()
        def cancel(): dialog.destroy()
        buttons = ttk.Frame(dialog); buttons.grid(row=len(fields), column=0, columnspan=2, sticky="e", padx=12, pady=12)
        ttk.Button(buttons, text="Cancelar", command=cancel).pack(side="right", padx=(6, 0)); ttk.Button(buttons, text="Salvar", command=accept, style="Primary.TButton").pack(side="right")
        dialog.bind("<Escape>", lambda _e: cancel()); dialog.bind("<Return>", lambda _e: accept()); self.wait_window(dialog)
        return result["value"]

    def _current_registry_table(self):
        selected = self.registry_book.nametowidget(self.registry_book.select())
        return selected

    def _get_registry_item(self, table):
        row = table.selected_values()
        if not row: self._selected_id(table); return None
        item_id = int(row[0])
        if table is self.specialty_table: return self.specialties.get(item_id)
        if table is self.office_table: return self.offices.get(item_id)
        return self.professionals.get(item_id)

    def create_registry_item(self):
        table = self._current_registry_table()
        try:
            if table is self.specialty_table:
                v = self._prompt("Nova especialidade", [("codigo", "Código"), ("nome", "Nome"), ("tempo", "Tempo médio (minutos)")])
                if v: self.specialties.create(Especialidade(nome=v["nome"], codigo=v["codigo"], tempo_medio=int(v["tempo"]))); self._audit("Criou especialidade", "especialidades")
            elif table is self.office_table:
                v = self._prompt("Novo consultório", [("numero", "Número"), ("descricao", "Descrição")])
                if v: self.offices.create(Consultorio(numero=v["numero"], descricao=v["descricao"] or None)); self._audit("Criou consultório", "consultorios")
            else:
                v = self._prompt("Novo profissional", [("nome", "Nome"), ("registro", "Registro"), ("especialidade", "ID da especialidade"), ("consultorio", "ID do consultório")])
                if v: self.professionals.create(Profissional(nome=v["nome"], registro=v["registro"], especialidade_id=int(v["especialidade"]), consultorio_id=int(v["consultorio"]))); self._audit("Criou profissional", "profissionais")
            self.refresh()
        except Exception as exc: self.message.show(f"Não foi possível salvar: {exc}", error=True)

    def edit_registry_item(self):
        table = self._current_registry_table(); item = self._get_registry_item(table)
        if item is None: return
        try:
            if table is self.specialty_table:
                fields = [("codigo", "Código"), ("nome", "Nome"), ("tempo", "Tempo médio (minutos)")]; initial = {"codigo": item.codigo, "nome": item.nome, "tempo": str(item.tempo_medio)}
                v = self._prompt("Editar especialidade", fields, initial)
                if v: item.codigo, item.nome, item.tempo_medio = v["codigo"], v["nome"], int(v["tempo"]); self.specialties.update(item); self._audit("Editou especialidade", "especialidades", item.id)
            elif table is self.office_table:
                v = self._prompt("Editar consultório", [("numero", "Número"), ("descricao", "Descrição")], {"numero": item.numero, "descricao": item.descricao or ""})
                if v: item.numero, item.descricao = v["numero"], v["descricao"] or None; self.offices.update(item); self._audit("Editou consultório", "consultorios", item.id)
            else:
                initial = {"nome": item.nome, "registro": item.registro, "especialidade": str(item.especialidade_id), "consultorio": str(item.consultorio_id)}
                fields = [("nome", "Nome"), ("registro", "Registro"), ("especialidade", "ID da especialidade"), ("consultorio", "ID do consultório")]
                v = self._prompt("Editar profissional", fields, initial)
                if v: item.nome, item.registro = v["nome"], v["registro"]; item.especialidade_id, item.consultorio_id = int(v["especialidade"]), int(v["consultorio"]); self.professionals.update(item); self._audit("Editou profissional", "profissionais", item.id)
            self.refresh()
        except Exception as exc: self.message.show(f"Não foi possível atualizar: {exc}", error=True)

    def toggle_registry_item(self):
        table = self._current_registry_table(); item = self._get_registry_item(table)
        if item is None: return
        item.ativo = not item.ativo
        try:
            if table is self.specialty_table: self.specialties.update(item); entity = "especialidades"
            elif table is self.office_table: self.offices.update(item); entity = "consultorios"
            else: self.professionals.update(item); entity = "profissionais"
            self._audit("Ativou" if item.ativo else "Desativou", entity, item.id); self.refresh()
        except Exception as exc:
            item.ativo = not item.ativo; self.message.show(f"Não foi possível alterar o status: {exc}", error=True)

    def create_user(self):
        v = self._prompt("Criar usuário", [("login", "Login"), ("perfil", "Perfil: Administrador / Recepção / Profissional / Coordenação"), ("senha", "Senha inicial")])
        if not v: return
        try:
            if len(v["senha"]) < 8: raise ValueError("A senha deve ter pelo menos 8 caracteres.")
            user = Usuario(login=v["login"], senha_hash=self.auth.hash_password(v["senha"]), perfil=PerfilUsuario(v["perfil"]))
            self.users.create(user); self._audit("Criou usuário", "usuarios", user.id); self.refresh()
        except Exception as exc: self.message.show(f"Não foi possível criar usuário: {exc}", error=True)

    def _selected_user(self):
        user_id = self._selected_id(self.user_table)
        return self.connection.execute("SELECT id, login, perfil, ativo FROM usuarios WHERE id=?", (user_id,)).fetchone() if user_id is not None else None

    def change_user_profile(self):
        row = self._selected_user()
        if row is None: return
        value = simpledialog.askstring("Perfil", f"Perfis: {', '.join(self.PERFIS)}", initialvalue=row["perfil"], parent=self)
        if value is None: return
        try:
            profile = PerfilUsuario(value.strip())
            if row["perfil"] == PerfilUsuario.ADMINISTRADOR.value and profile != PerfilUsuario.ADMINISTRADOR:
                count = self.connection.execute("SELECT COUNT(*) FROM usuarios WHERE perfil=? AND ativo=1", (PerfilUsuario.ADMINISTRADOR.value,)).fetchone()[0]
                if row["ativo"] and count <= 1: raise ValueError("Não é permitido remover o último administrador ativo.")
            self.connection.execute("UPDATE usuarios SET perfil=? WHERE id=?", (profile.value, row["id"])); self.connection.commit()
            self._audit("Alterou perfil", "usuarios", row["id"]); self.refresh()
        except Exception as exc: self.message.show(f"Perfil inválido ou alteração recusada: {exc}", error=True)

    def reset_user_password(self):
        row = self._selected_user()
        if row is None: return
        password = simpledialog.askstring("Redefinir senha", "Nova senha (mínimo 8 caracteres):", show="*", parent=self)
        if password is None: return
        if len(password) < 8: self.message.show("A senha deve ter pelo menos 8 caracteres.", error=True); return
        self.connection.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (self.auth.hash_password(password), row["id"])); self.connection.commit()
        self._audit("Redefiniu senha", "usuarios", row["id"]); self.message.show("Senha redefinida.", success=True)

    def toggle_user(self):
        row = self._selected_user()
        if row is None: return
        active = not bool(row["ativo"])
        if not active and row["perfil"] == PerfilUsuario.ADMINISTRADOR.value:
            count = self.connection.execute("SELECT COUNT(*) FROM usuarios WHERE perfil=? AND ativo=1", (PerfilUsuario.ADMINISTRADOR.value,)).fetchone()[0]
            if count <= 1: self.message.show("Não é permitido desativar o último administrador ativo.", error=True); return
        if not messagebox.askyesno("Confirmar", f"{'Ativar' if active else 'Desativar'} o usuário {row['login']}?", parent=self): return
        self.users.set_active(row["id"], active); self._audit("Ativou usuário" if active else "Desativou usuário", "usuarios", row["id"]); self.refresh()

    def save_settings(self):
        try:
            parsed = {key: int(var.get()) for key, var in self.setting_vars.items()}
            if parsed["tempo_medio_padrao"] < 1 or parsed["intervalo_rechamada_segundos"] < 1 or parsed["alternancia_normal_preferencial"] < 1: raise ValueError("Tempos e alternância devem ser maiores que zero.")
            if parsed["sequencia_diaria"] not in (0, 1): raise ValueError("Sequência diária deve ser 0 ou 1.")
            for key, value in parsed.items(): self.settings.set(key, str(value))
            self._audit("Atualizou parâmetros", "configuracoes"); self.message.show("Parâmetros salvos.", success=True)
        except (ValueError, TypeError) as exc: self.message.show(f"Parâmetros inválidos: {exc}", error=True)

    def generate_report(self):
        try:
            start, end = date.fromisoformat(self.report_start.get().strip()), date.fromisoformat(self.report_end.get().strip())
            if end < start: raise ValueError("A data final deve ser igual ou posterior à inicial.")
            rows = self.connection.execute("""SELECT e.codigo,e.nome,a.inicio,a.fim,p.nome profissional,s.status FROM senhas s JOIN especialidades e ON e.id=s.especialidade_id LEFT JOIN atendimentos a ON a.senha_id=s.id LEFT JOIN profissionais p ON p.id=a.profissional_id WHERE date(s.criada_em) BETWEEN date(?) AND date(?) ORDER BY e.codigo,p.nome""", (start.isoformat(), end.isoformat())).fetchall()
            self.report_table.clear(); by_specialty = {}; by_professional = {}; counts = {}
            for row in rows:
                if row["status"] in ("Ausente", "Cancelada"): counts[row["status"]] = counts.get(row["status"], 0) + 1
                if row["status"] != "Finalizada" or not row["inicio"] or not row["fim"]: continue
                mins = (datetime.fromisoformat(row["fim"]) - datetime.fromisoformat(row["inicio"])).total_seconds()/60
                if mins < 0: continue
                spec = f"Especialidade {row['codigo']} — {row['nome']}"; by_specialty.setdefault(spec, []).append(mins)
                if row["profissional"]: by_professional.setdefault(f"Profissional {row['profissional']} ({row['codigo']})", []).append(mins)
            for label, values in sorted(by_specialty.items()): self.report_table.add_row((label, len(values), f"{sum(values)/len(values):.2f}"))
            for label, values in sorted(by_professional.items()): self.report_table.add_row((label, len(values), f"{sum(values)/len(values):.2f}"))
            for label, count in sorted(counts.items()): self.report_table.add_row((label, count, "—"))
            if not rows: self.report_table.add_row(("Sem registros no período", 0, "—"))
            self._audit("Gerou relatório", "atendimentos", details=f"{start.isoformat()} a {end.isoformat()}")
            self.message.show(f"Relatório gerado: {start.isoformat()} a {end.isoformat()}.", success=True)
        except Exception as exc: self.message.show(f"Não foi possível gerar relatório: {exc}", error=True)

    def create_backup(self):
        try:
            path = self.backup.create_backup(DATABASE_PATH.parent / "backups")
            self._audit("Criou backup", "backup", details=str(path)); self.refresh_backups(); self.message.show(f"Backup criado: {path}", success=True)
        except Exception as exc: self.message.show(f"Falha ao criar backup: {exc}", error=True)

    def restore_backup(self):
        values = self.backup_table.selected_values()
        if not values: self.message.show("Selecione um backup.", error=True); return
        path = Path(values[1])
        if not messagebox.askyesno("Confirmar restauração", f"Substituir o banco ativo pelo arquivo?\n{path}\n\nUma cópia do banco atual será criada.", parent=self): return
        try:
            safety = self.backup.create_backup(DATABASE_PATH.parent / "backups", prefix="antes_restauracao")
            self.backup.restore_backup(path); self._audit("Restaurou backup", "backup", details=f"{path}; segurança={safety}")
            self.refresh(); self.refresh_backups(); self.message.show("Backup restaurado. Reinicie a aplicação para garantir uma sessão limpa.", success=True)
        except Exception as exc: self.message.show(f"Falha ao restaurar backup: {exc}", error=True)

    def refresh_backups(self):
        if not hasattr(self, "backup_table"): return
        self.backup_table.clear()
        for path in self.backup.list_backups(DATABASE_PATH.parent / "backups"): self.backup_table.add_row((path.name, str(path)))

    def _audit(self, action, entity, entity_id=None, details=None): self.audit.record(action, entity, entity_id, details)

    def refresh(self):
        try:
            self.specialty_table.clear()
            for item in self.specialties.list(): self.specialty_table.add_row((item.id,item.codigo,item.nome,item.tempo_medio,"Sim" if item.ativo else "Não"))
            self.office_table.clear()
            for item in self.offices.list(): self.office_table.add_row((item.id,item.numero,item.descricao or "","Sim" if item.ativo else "Não"))
            spec_names = {x.id:f"{x.codigo} — {x.nome}" for x in self.specialties.list()}; office_names = {x.id:x.numero for x in self.offices.list()}
            self.professional_table.clear()
            for item in self.professionals.list(): self.professional_table.add_row((item.id,item.nome,item.registro,spec_names.get(item.especialidade_id,item.especialidade_id),office_names.get(item.consultorio_id,item.consultorio_id),"Sim" if item.ativo else "Não"))
            self.user_table.clear()
            for row in self.connection.execute("SELECT id,login,perfil,ativo FROM usuarios ORDER BY login"): self.user_table.add_row((row["id"],row["login"],row["perfil"],"Sim" if row["ativo"] else "Não"))
            for key,var in self.setting_vars.items():
                if not var.get().strip(): var.set(self.settings.get(key, "") or "")
            self.refresh_backups(); self.message.show("Dados administrativos atualizados.", success=True)
        except Exception as exc: self.message.show(f"Erro ao atualizar dados: {exc}", error=True)

if __name__ == "__main__":
    from database.connection import Database
    root=tk.Tk(); root.title("Administração"); root.geometry("1000x700")
    with Database(":memory:") as database:
        AuthService(database.connection).ensure_default_users()
        view=AdminView(root,database.connection); view.grid(row=0,column=0,sticky="nsew"); root.columnconfigure(0,weight=1); root.rowconfigure(0,weight=1); root.mainloop()
