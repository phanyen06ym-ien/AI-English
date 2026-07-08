from database.auth import login_user


def print_user(username, password):
    """In kết quả test đăng nhập ra terminal."""
    try:
        user = login_user(username, password)
    except Exception as exc:
        print(f"{username}: lỗi database - {exc}")
        return

    print(f"{username}: {user}")


if __name__ == "__main__":
    print_user("admin", "123456")
    print_user("student1", "123456")
    print_user("admin", "sai")
