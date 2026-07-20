import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: page

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: 230

            RowLayout {
                anchors.fill: parent
                anchors.margins: 26
                spacing: 22

                Rectangle {
                    Layout.preferredWidth: 112
                    Layout.preferredHeight: 112
                    radius: 56
                    color: "#FBE4CA"

                    Label {
                        anchors.centerIn: parent
                        text: authController ? (authController.currentUser.username || "U").charAt(0).toUpperCase() : "U"
                        color: "#222222"
                        font.pixelSize: 42
                        font.bold: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: authController ? (authController.currentUser.fullname || "Người dùng") : "Người dùng"
                        color: "#222222"
                        font.family: "Segoe UI"
                        font.pixelSize: 26
                        font.bold: true
                    }

                    Label {
                        text: "username: " + (authController ? (authController.currentUser.username || "") : "")
                        color: "#777777"
                        font.family: "Segoe UI"
                        font.pixelSize: 15
                    }

                    Label {
                        text: authController ? authController.statusMessage : ""
                        visible: authController && authController.statusMessage.length > 0
                        color: authController && authController.statusMessage.indexOf("thành công") >= 0 ? "#2D7D46" : "#B94C3D"
                        font.family: "Segoe UI"
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }

                    RowLayout {
                        Layout.topMargin: 12
                        spacing: 10

                        PrimaryButton {
                            text: "Đổi mật khẩu"
                            enabled: authController && !authController.loading
                            onClicked: changePasswordDialog.open()
                        }

                        PrimaryButton {
                            text: "Đăng xuất"
                            enabled: authController && !authController.loading
                            onClicked: authController.logout()
                        }
                    }
                }
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 10

                SectionTitle { text: "Thông tin ứng dụng" }
                Divider { Layout.fillWidth: true }

                Label {
                    text: "AI-English"
                    color: "#222222"
                    font.family: "Segoe UI"
                    font.pixelSize: 18
                    font.bold: true
                }

                Label {
                    text: "Ứng dụng nhận dạng vật thể bằng YOLOv8, hỗ trợ học từ vựng tiếng Anh qua ảnh, webcam, lịch sử và thống kê."
                    color: "#777777"
                    font.family: "Segoe UI"
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }

    Dialog {
        id: changePasswordDialog
        title: "Đổi mật khẩu"
        modal: true
        standardButtons: Dialog.NoButton
        width: 420

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            PasswordField {
                id: oldPassword
                placeholderText: "Mật khẩu hiện tại"
                Layout.fillWidth: true
            }

            PasswordField {
                id: newPassword
                placeholderText: "Mật khẩu mới"
                Layout.fillWidth: true
            }

            PasswordField {
                id: confirmPassword
                placeholderText: "Xác nhận mật khẩu mới"
                Layout.fillWidth: true
            }

            Label {
                text: authController ? authController.statusMessage : ""
                visible: authController && authController.statusMessage.length > 0
                color: authController && authController.statusMessage.indexOf("thành công") >= 0 ? "#2D7D46" : "#B94C3D"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.alignment: Qt.AlignRight

                Button {
                    text: "Hủy"
                    onClicked: changePasswordDialog.close()
                }

                PrimaryButton {
                    text: authController && authController.loading ? "Đang lưu..." : "Lưu"
                    enabled: authController && !authController.loading
                    onClicked: authController.changePassword(
                        oldPassword.text,
                        newPassword.text,
                        confirmPassword.text
                    )
                }
            }
        }

        Connections {
            target: authController

            function onPasswordChanged() {
                oldPassword.text = ""
                newPassword.text = ""
                confirmPassword.text = ""
                changePasswordDialog.close()
            }
        }
    }
}
