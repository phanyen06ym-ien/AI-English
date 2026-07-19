# test/test_knn.py

from ml.knn import (
    get_related_words,
    train_knn_model
)


def print_results(word, n=3):

    print("\n" + "=" * 60)

    print(
        f"TEST KNN VỚI TỪ: {word}"
    )

    print("=" * 60)

    results = get_related_words(
        word,
        n=n
    )

    if not results:

        print(
            "Không tìm thấy từ trong dataset!"
        )

        return

    print(
        f"Tìm thấy {len(results)} từ liên quan:"
    )

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"\n{index}. {item['english']}"
        )

        print(
            f"   Nghĩa: {item['vietnamese']}"
        )

        print(
            f"   Chủ đề: {item['category']}"
        )

        print(
            f"   Trình độ: {item['level']}"
        )


def test_existing_words():

    print("\n")
    print("#" * 60)
    print("# TEST 1: TỪ CÓ TRONG DATASET")
    print("#" * 60)

    words = [
        "laptop",
        "computer",
        "book",
        "bottle",
        "cat"
    ]

    for word in words:

        print_results(
            word,
            n=3
        )


def test_unknown_word():

    print("\n")
    print("#" * 60)
    print("# TEST 2: TỪ KHÔNG CÓ TRONG DATASET")
    print("#" * 60)

    word = "this_word_does_not_exist"

    results = get_related_words(
        word,
        n=3
    )

    if not results:

        print(
            "PASS: Hệ thống xử lý đúng từ không tồn tại."
        )

    else:

        print(
            "FAIL: Từ không tồn tại nhưng vẫn trả về kết quả."
        )


def test_different_number_of_results():

    print("\n")
    print("#" * 60)
    print("# TEST 3: KIỂM TRA SỐ LƯỢNG KẾT QUẢ")
    print("#" * 60)

    word = "laptop"

    for n in [1, 3, 5]:

        results = get_related_words(
            word,
            n=n
        )

        print(
            f"\nYêu cầu {n} kết quả:"
        )

        print(
            f"Thực tế trả về: {len(results)} kết quả"
        )

        for item in results:

            print(
                f"- {item['english']}"
            )


def test_result_structure():

    print("\n")
    print("#" * 60)
    print("# TEST 4: KIỂM TRA CẤU TRÚC KẾT QUẢ")
    print("#" * 60)

    word = "laptop"

    results = get_related_words(
        word,
        n=3
    )

    required_fields = [
        "english",
        "vietnamese",
        "category",
        "level"
    ]

    for item in results:

        for field in required_fields:

            if field in item:

                print(
                    f"PASS: Có trường {field}"
                )

            else:

                print(
                    f"FAIL: Thiếu trường {field}"
                )


def test_no_duplicate_results():

    print("\n")
    print("#" * 60)
    print("# TEST 5: KIỂM TRA TỪ KHÔNG BỊ TRÙNG")
    print("#" * 60)

    word = "laptop"

    results = get_related_words(
        word,
        n=10
    )

    words = [
        item["english"]
        for item in results
    ]

    if len(words) == len(set(words)):

        print(
            "PASS: Không có từ bị trùng."
        )

    else:

        print(
            "FAIL: Có từ bị trùng."
        )


def test_input_case():

    print("\n")
    print("#" * 60)
    print("# TEST 6: KIỂM TRA CHỮ HOA / CHỮ THƯỜNG")
    print("#" * 60)

    words = [
        "laptop",
        "LAPTOP",
        "Laptop"
    ]

    for word in words:

        results = get_related_words(
            word,
            n=3
        )

        print(
            f"{word}: "
            f"{len(results)} kết quả"
        )


def test_empty_input():

    print("\n")
    print("#" * 60)
    print("# TEST 7: KIỂM TRA INPUT RỖNG")
    print("#" * 60)

    test_inputs = [
        "",
        " ",
        None
    ]

    for word in test_inputs:

        try:

            results = get_related_words(
                word,
                n=3
            )

            print(
                f"Input {repr(word)}: "
                f"Xử lý thành công"
            )

        except Exception as error:

            print(
                f"Input {repr(word)}: "
                f"Lỗi - {error}"
            )


def main():

    print("\n")
    print("*" * 60)
    print("* BẮT ĐẦU KIỂM THỬ THUẬT TOÁN KNN")
    print("*" * 60)

    test_existing_words()

    test_unknown_word()

    test_different_number_of_results()

    test_result_structure()

    test_no_duplicate_results()

    test_input_case()

    test_empty_input()

    print("\n")
    print("*" * 60)
    print("* HOÀN TẤT KIỂM THỬ KNN")
    print("*" * 60)


if __name__ == "__main__":

    main()