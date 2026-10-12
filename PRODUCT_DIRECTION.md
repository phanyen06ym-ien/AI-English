# PRODUCT_DIRECTION — EnglishGo

**Project:** EnglishGo — AI Visual Vocabulary Learning
**Course:** Software Engineering (INFO2005)
**Development Direction:** Upgrade Existing Project
**Original Repository:** https://github.com/phanyen06ym-ien/AI-English
**Status:** Draft — Week 01

## 1. Existing Product

AI-English là ứng dụng desktop phát triển bằng Python, sử dụng PySide6/QML để xây dựng giao diện.

Theo README và mã nguồn hiện tại, ứng dụng sử dụng:

- YOLO để nhận diện vật thể từ ảnh hoặc webcam.
- Bộ dữ liệu từ vựng để ánh xạ vật thể sang tiếng Anh và tiếng Việt.
- k-NN để đề xuất các từ liên quan.
- K-Means để phân nhóm từ vựng.
- PostgreSQL để lưu lịch sử nhận diện.

## 2. Problem Statement

Định hướng nâng cấp đặt ra các vấn đề cần giải quyết:

- Phần mềm hiện tại chạy trên desktop, chưa đáp ứng mục tiêu sử dụng trực tiếp trên web.
- Cần bổ sung quy trình học từ vựng cá nhân: lưu từ, ôn tập và kiểm tra.
- Cần thiết kế quy trình người dùng kiểm tra, lựa chọn và xác nhận kết quả AI.
- Cần quản lý quyền riêng tư, lượt sử dụng AI và dữ liệu học tập.

Các vấn đề trên là khoảng cách giữa sản phẩm hiện tại và mục tiêu EnglishGo; không mặc nhiên khẳng định tất cả đều là lỗi đã kiểm chứng của mã nguồn cũ.

## 3. Product Vision

EnglishGo là ứng dụng web hỗ trợ học từ vựng tiếng Anh thông qua nhận diện vật thể trong hình ảnh, cho phép người học khám phá từ vựng từ môi trường thực tế, lưu từ cần học và ôn tập bằng Quiz.

AI đóng vai trò hỗ trợ đề xuất từ vựng. Người dùng giữ quyền quyết định từ nào được lưu và sử dụng trong hoạt động học tập.

## 4. Target Users

**Guest:** Có thể tải ảnh lên, xem các vật thể được nhận diện và thông tin từ vựng, trong giới hạn sử dụng AI.

**Learner:** Có tài khoản, có thể lưu từ vựng, quản lý My Vocabulary, làm Quiz và xem lịch sử kết quả.

**Admin:** Vai trò quản trị dự kiến; phạm vi chức năng và quyền truy cập cần được xác định chi tiết trước khi triển khai.

## 5. Proposed MVP Scope

1. Đăng ký, đăng nhập và quản lý phiên người dùng.
2. Tải ảnh tĩnh, xem trước và xử lý vùng ảnh nhạy cảm trước khi gửi AI.
3. Nhận diện nhiều vật thể và hiển thị kết quả để người dùng lựa chọn.
4. Ánh xạ nhãn AI với mục từ chuẩn có nghĩa tiếng Việt, từ loại và ví dụ.
5. Lưu, tìm kiếm và xóa từ vựng cá nhân.
6. Làm Quiz từ danh sách từ đã lưu.
7. Lưu lịch sử Quiz hoàn thành.
8. Kiểm soát lượt phân tích AI và quyền riêng tư ở mức MVP.

## 6. Upgrade Strategy

**Review:** Phân tích mã nguồn AI-English, xác định chức năng và giới hạn thực tế.

**Reuse:** Ưu tiên đánh giá khả năng tái sử dụng thuật toán nhận diện, xử lý từ vựng, dữ liệu và kiểm thử.

**Adapt:** Điều chỉnh các module phù hợp để phục vụ kiến trúc ứng dụng web.

**Replace:** Thay thế những thành phần không đáp ứng mục tiêu mới, chẳng hạn giao diện desktop, sau khi thiết kế kiến trúc được phê duyệt.

**Verify:** Kiểm thử hồi quy để chứng minh phần được tái sử dụng vẫn hoạt động đúng.

## 7. AI Feature

**Feature:** Multi-Object Image Recognition for Vocabulary Learning.

- Input: Ảnh tĩnh được người dùng chủ động gửi.
- Processing: Nhận diện vật thể và ánh xạ sang từ vựng chuẩn.
- Output: Danh sách vật thể, vị trí nhận diện, độ tin cậy và các mục từ phù hợp.
- Human Control: Người dùng chọn, bỏ qua hoặc thay thế nhãn bằng từ được hỗ trợ.
- Safety: Không mặc định lưu ảnh gốc dài hạn; cần xác nhận trước khi gửi ảnh cho dịch vụ AI bên ngoài nếu sử dụng.

## 8. Initial Technical Direction

- Frontend: Responsive Web — công nghệ chưa chốt.
- Backend: Đánh giá tái sử dụng các module Python hiện có.
- Database: PostgreSQL trên Supabase.
- AI: Đánh giá khả năng tái sử dụng YOLO và vocabulary mapping.
- ORM / Data Access: Chưa chốt; phần mềm gốc sử dụng psycopg2 và dataclass.
- Deployment: Chưa quyết định.

## 9. Success Criteria

- Người dùng thực hiện được luồng từ tải ảnh đến xem từ vựng.
- Learner lưu được từ vựng hợp lệ và ôn tập bằng Quiz.
- Kết quả AI được kiểm tra và xử lý khi nhận diện sai hoặc không hỗ trợ.
- Các chức năng cốt lõi có acceptance criteria và test tương ứng.
- Có minh chứng sử dụng AI Agent, human review, GitHub Issues và Pull Requests.
- Không đưa secrets vào repository.

## 10. Open Decisions

- Kiến trúc frontend/backend và framework phù hợp.
- Giải pháp authentication.
- Phạm vi chức năng Admin trong MVP.
- ORM, migration và schema database.
- Nguồn cung cấp AI inference.
- Cách triển khai quota cho Guest và Learner.
- Hosting, chi phí vận hành và giới hạn tài nguyên.

**Next:** Review codebase, hoàn thiện AGENT_GUIDE.md, AI_USAGE_POLICY.md và nhật ký Week 01.
