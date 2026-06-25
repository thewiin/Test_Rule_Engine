# Test Rule Engine

**VPBank Technology Hackathon 2025**  
**Group 117 - EDA - DPC - Challenge #24**

Dự án **Test Rule Engine** là một hệ thống tự động hóa việc kiểm tra tính chính xác của dữ liệu (Data Accuracy Test) dựa trên nền tảng web. Thay vì phải viết thủ công các câu lệnh SQL phức tạp, người dùng có thể định nghĩa các logic kiểm tra thông qua các file cấu hình JSON được chuẩn hóa. 

Hệ thống sẽ tự động phân tích (parse), tạo ra câu truy vấn SQL (generate SQL), thực thi kiểm tra trên cơ sở dữ liệu và xuất báo cáo kết quả chi tiết (PASS/FAIL) – tất cả đều không yêu cầu người dùng phải có chuyên môn sâu về kỹ thuật.

---

## Luồng hoạt động (Workflow)

Hệ thống hoạt động dựa trên luồng dữ liệu (Data Flow) bao gồm các thành phần chính sau:

### 1. Lớp định nghĩa Rule (User Interface & Rule Store)
- Người dùng tương tác với hệ thống thông qua giao diện Web theo từng bước:
  - Chọn nguồn dữ liệu (Scheme, Tables).
  - Chọn cột dữ liệu cần kiểm tra (Columns Specification).
  - Chọn loại Rule (Từ 5 loại cấu hình sẵn: *Value Range, Value Template, Data Continuity/Integrity, Same Group Statistical, Different Group Statistical*).
  - Định nghĩa các tham số, ngưỡng (Thresholds, Patterns).
  - Kết hợp các logic (AND/OR/NOT).
- Cấu hình này được lưu trữ dưới dạng định dạng **JSON** có thể đọc hiểu và dễ dàng tái sử dụng.

### 2. Xử lý Rule (Rule Parser & Validator)
- Khi nhận yêu cầu từ người dùng, hệ thống sẽ tiến hành phân tích cú pháp (Parse) file JSON.
- Validate các cấu hình rule dựa trên các ràng buộc nghiệp vụ (Business logic constraints).
- Đảm bảo tính hợp lệ của rule trước khi chuyển sang bước tạo truy vấn.

### 3. Trình tạo SQL (SQL Generation Engine)
- Tiếp nhận các Rule đã được xử lý và chuyển đổi chúng thành các câu lệnh SQL.
- Tự động gắn tham số (Parameterized SQL) để ngăn chặn SQL Injection.
- Áp dụng các cú pháp tương thích với cơ sở dữ liệu (PostgreSQL) và hỗ trợ tối ưu hóa truy vấn cho tập dữ liệu lớn.

### 4. Thực thi và Giám sát (Execution & Monitoring Layer)
- **Thực thi SQL:** Hệ thống chạy trực tiếp các câu lệnh SQL đã được tạo ra trên cơ sở dữ liệu PostgreSQL.
- **Xử lý kết quả:** Chuyển đổi kết quả SQL thành trạng thái kiểm tra thân thiện với nghiệp vụ (PASS/FAIL).
- **Ghi log & Trích xuất:**
  - Ghi nhận lại toàn bộ lịch sử (Audit trail), số lượng bản ghi PASS/FAIL và thông báo lỗi.
  - Hỗ trợ tải xuống kết quả dưới dạng file **.csv** chi tiết từng dòng dữ liệu (record_id, status, error_message) để phục vụ cho các công cụ BI hoặc Excel.

---

## Giá trị cốt lõi (USP)

> **“No SQL, no manual checks - just upload your rules and receive reliable validation results - instantly.”**

Hệ thống cung cấp một quy trình khép kín, tối giản hóa việc đảm bảo chất lượng dữ liệu (QC), tiết kiệm thời gian tạo test script, và giảm thiểu rủi ro từ các lỗi dữ liệu ẩn trong các hệ thống cốt lõi.