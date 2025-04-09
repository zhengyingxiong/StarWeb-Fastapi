from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "permissions" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "code" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "type" VARCHAR(20) NOT NULL,
    "path" VARCHAR(200),
    "sort_order" INT NOT NULL  DEFAULT 0,
    "parent_id" INT REFERENCES "permissions" ("id") ON DELETE SET NULL
);
COMMENT ON COLUMN "permissions"."created_at" IS '创建时间';
COMMENT ON COLUMN "permissions"."updated_at" IS '更新时间';
COMMENT ON COLUMN "permissions"."is_deleted" IS '是否逻辑删除';
COMMENT ON COLUMN "permissions"."deleted_at" IS '删除时间';
COMMENT ON COLUMN "permissions"."id" IS '主键ID';
COMMENT ON COLUMN "permissions"."name" IS '权限名称';
COMMENT ON COLUMN "permissions"."code" IS '权限代码';
COMMENT ON COLUMN "permissions"."description" IS '权限描述';
COMMENT ON COLUMN "permissions"."type" IS '权限类型';
COMMENT ON COLUMN "permissions"."path" IS '路由路径';
COMMENT ON COLUMN "permissions"."sort_order" IS '排序序号';
COMMENT ON COLUMN "permissions"."parent_id" IS '父权限';
COMMENT ON TABLE "permissions" IS '权限表';
CREATE TABLE IF NOT EXISTS "roles" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "code" VARCHAR(50) NOT NULL UNIQUE,
    "description" TEXT,
    "is_system" BOOL NOT NULL  DEFAULT False
);
COMMENT ON COLUMN "roles"."created_at" IS '创建时间';
COMMENT ON COLUMN "roles"."updated_at" IS '更新时间';
COMMENT ON COLUMN "roles"."is_deleted" IS '是否逻辑删除';
COMMENT ON COLUMN "roles"."deleted_at" IS '删除时间';
COMMENT ON COLUMN "roles"."id" IS '主键ID';
COMMENT ON COLUMN "roles"."name" IS '角色名称';
COMMENT ON COLUMN "roles"."code" IS '角色代码';
COMMENT ON COLUMN "roles"."description" IS '角色描述';
COMMENT ON COLUMN "roles"."is_system" IS '是否系统内置';
COMMENT ON TABLE "roles" IS '角色表';
CREATE TABLE IF NOT EXISTS "users" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL  DEFAULT False,
    "deleted_at" TIMESTAMPTZ,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "password_hash" VARCHAR(128) NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_superadmin" BOOL NOT NULL  DEFAULT False,
    "last_login" TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
COMMENT ON COLUMN "users"."created_at" IS '创建时间';
COMMENT ON COLUMN "users"."updated_at" IS '更新时间';
COMMENT ON COLUMN "users"."is_deleted" IS '是否逻辑删除';
COMMENT ON COLUMN "users"."deleted_at" IS '删除时间';
COMMENT ON COLUMN "users"."id" IS '主键ID';
COMMENT ON COLUMN "users"."password_hash" IS '密码哈希';
COMMENT ON COLUMN "users"."username" IS '用户名';
COMMENT ON COLUMN "users"."email" IS '邮箱地址';
COMMENT ON COLUMN "users"."is_active" IS '是否激活';
COMMENT ON COLUMN "users"."is_superadmin" IS '是否是超级管理员';
COMMENT ON COLUMN "users"."last_login" IS '最后登录时间';
COMMENT ON TABLE "users" IS '用户信息表';
CREATE TABLE IF NOT EXISTS "user_roles" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "data_scope" VARCHAR(20) NOT NULL  DEFAULT 'self',
    "role_id" INT NOT NULL REFERENCES "roles" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_roles_user_id_63f1a8" UNIQUE ("user_id", "role_id")
);
COMMENT ON COLUMN "user_roles"."created_at" IS '创建时间';
COMMENT ON COLUMN "user_roles"."updated_at" IS '更新时间';
COMMENT ON COLUMN "user_roles"."id" IS '主键ID';
COMMENT ON COLUMN "user_roles"."data_scope" IS '数据权限范围';
COMMENT ON COLUMN "user_roles"."role_id" IS '角色';
COMMENT ON COLUMN "user_roles"."user_id" IS '用户';
COMMENT ON TABLE "user_roles" IS '用户角色关联表';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "roles_permissions" (
    "roles_id" INT NOT NULL REFERENCES "roles" ("id") ON DELETE CASCADE,
    "permission_id" INT NOT NULL REFERENCES "permissions" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "roles_permissions" IS '角色拥有的权限';
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_roles_permi_roles_i_74c3df" ON "roles_permissions" ("roles_id", "permission_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
