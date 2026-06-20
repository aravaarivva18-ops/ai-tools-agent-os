from dashboard_mvp.db import Base
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="manager") # admin, manager, client
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Связи
    client = relationship("Client", back_populates="users")
    managed_projects = relationship("Project", back_populates="manager")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active") # active, paused

    # Связи
    users = relationship("User", back_populates="client")
    projects = relationship("Project", back_populates="client")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Связи
    client = relationship("Client", back_populates="projects")
    manager = relationship("User", back_populates="managed_projects")
    integrations = relationship("Integration", back_populates="project", cascade="all, delete-orphan")
    source_mapping = relationship("SourceMapping", uselist=False, back_populates="project", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStat", back_populates="project", cascade="all, delete-orphan")
    kpi_plans = relationship("KPIPlan", back_populates="project", cascade="all, delete-orphan")
    change_logs = relationship("ChangeLog", back_populates="project", cascade="all, delete-orphan")

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String, nullable=False, default="yandex") # yandex
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True) # Время истечения access_token

    # Связи
    project = relationship("Project", back_populates="integrations")

class SourceMapping(Base):
    __tablename__ = "source_mappings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    direct_login = Column(String, nullable=True)
    metrika_counter_id = Column(String, nullable=True)
    # Храним ID целей в Метрике через запятую, например "320946135,320946351"
    lead_goals_ids = Column(String, nullable=True)
    mapping_details = Column(Text, nullable=True) # Доп. настройки в формате JSON

    # Связи
    project = relationship("Project", back_populates="source_mapping")

class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spent = Column(Float, default=0.0) # Расход бюджета
    leads = Column(Integer, default=0) # Количество лидов (конверсий)

    # Вычисляемые поля (для удобства кэширования, хотя можно считать на лету)
    cpl = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)

    # Связи
    project = relationship("Project", back_populates="daily_stats")

class KPIPlan(Base):
    __tablename__ = "kpi_plans"

    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, nullable=False, index=True) # Формат 'YYYY-MM'
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    budget_plan = Column(Float, default=0.0)
    leads_plan = Column(Integer, default=0)
    cpl_plan = Column(Float, default=0.0)

    # Связи
    project = relationship("Project", back_populates="kpi_plans")

class ChangeLog(Base):
    __tablename__ = "change_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    changes_description = Column(Text, nullable=False)
    comment = Column(Text, nullable=True)
    expected_effect = Column(Text, nullable=True)

    # Связи
    project = relationship("Project", back_populates="change_logs")
