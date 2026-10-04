from alembic import op
import sqlalchemy as sa
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    role = sa.Enum("client", "operator", "admin", name="role")
    quality = sa.Enum("good", "usable", "bad", name="quality")
    request_status = sa.Enum("submitted", "in_progress", "delivered", "accepted", "rejected", name="request_status")
    role.create(op.get_bind(), checkfirst=True); quality.create(op.get_bind(), checkfirst=True); request_status.create(op.get_bind(), checkfirst=True)
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("role", role, nullable=False), sa.Column("organisation", sa.String(255)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True); op.create_index("ix_users_role", "users", ["role"])
    op.create_table("episodes", sa.Column("episode_id", sa.String(64), primary_key=True), sa.Column("robot_id", sa.String(64), nullable=False), sa.Column("task_name", sa.String(255), nullable=False), sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False), sa.Column("duration_seconds", sa.Float(), nullable=False), sa.Column("operator_name", sa.String(255), nullable=False), sa.Column("quality", quality, nullable=False))
    for name,col in [("robot_id","robot_id"),("task_name","task_name"),("recorded_at","recorded_at"),("quality","quality")]: op.create_index("ix_episodes_"+name,"episodes",[col])
    op.create_index("ix_episodes_recorded_robot", "episodes", ["recorded_at", "robot_id"])
    op.create_table("dataset_requests", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("client_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("task_name", sa.String(255), nullable=False), sa.Column("episodes_requested", sa.Integer(), nullable=False), sa.Column("deadline", sa.DateTime(timezone=True), nullable=False), sa.Column("notes", sa.Text()), sa.Column("status", request_status, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for col in ["client_id","task_name","status"]: op.create_index("ix_dataset_requests_"+col,"dataset_requests",[col])
    op.create_table("assignments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("request_id", sa.Integer(), sa.ForeignKey("dataset_requests.id", ondelete="CASCADE"), nullable=False), sa.Column("episode_id", sa.String(64), sa.ForeignKey("episodes.episode_id", ondelete="RESTRICT"), nullable=False), sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("request_id","episode_id",name="uq_request_episode"))
    op.create_index("ix_assignments_request_id","assignments",["request_id"]); op.create_index("ix_assignments_episode_id","assignments",["episode_id"],unique=True)
    op.create_table("status_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("request_id", sa.Integer(), sa.ForeignKey("dataset_requests.id", ondelete="CASCADE"), nullable=False), sa.Column("from_status", sa.Enum("submitted", "in_progress", "delivered", "accepted", "rejected", name="history_from_status")), sa.Column("to_status", request_status, nullable=False), sa.Column("changed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_status_history_request_id","status_history",["request_id"]); op.create_index("ix_status_history_changed_at","status_history",["changed_at"])

def downgrade():
    op.drop_table("status_history"); op.drop_table("assignments"); op.drop_table("dataset_requests"); op.drop_table("episodes"); op.drop_table("users")
    for typ in ["history_from_status","request_status","quality","role"]: op.execute(sa.text(f"DROP TYPE IF EXISTS {typ}"))
