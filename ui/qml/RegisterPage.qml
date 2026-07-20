import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: page
    signal backToLoginRequested()

    Connections {
        target: authController

        function onRegisterSucceeded() {
            page.backToLoginRequested()
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#FAFAFA"
    }

    Card {
        width: 460
        height: 540
        anchors.centerIn: parent

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 12

            Label {
                text: "Tạo tài khoản"
                color: "#222222"
                font.family: "Segoe UI"
                font.pixelSize: 28
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            TextField {
                id: fullname
                placeholderText: "Họ và tên"
                selectByMouse: true
                Layout.fillWidth: true
                implicitHeight: 42
                leftPadding: 12
                background: Rectangle {
                    radius: 10
                    color: "#FFFFFF"
                    border.color: parent.activeFocus ? "#F6B26B" : "#E8E8E8"
                }
            }

            TextField {
                id: username
                placeholderText: "Tên đăng nhập"
                selectByMouse: true
                Layout.fillWidth: true
                implicitHeight: 42
                leftPadding: 12
                background: Rectangle {
                    radius: 10
                    color: "#FFFFFF"
                    border.color: parent.activeFocus ? "#F6B26B" : "#E8E8E8"
                }
            }

            PasswordField {
                id: password
                placeholderText: "Mật khẩu"
                Layout.fillWidth: true
            }

            PasswordField {
                id: confirmPassword
                placeholderText: "Xác nhận mật khẩu"
                Layout.fillWidth: true
            }

            Label {
                text: authController.statusMessage
                visible: authController.statusMessage.length > 0
                color: authController.statusMessage.indexOf("thành công") >= 0 ? "#2D7D46" : "#B94C3D"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            PrimaryButton {
                text: authController.loading ? "Đang tạo..." : "Tạo tài khoản"
                enabled: !authController.loading
                Layout.fillWidth: true
                onClicked: authController.register(
                    fullname.text,
                    username.text,
                    password.text,
                    confirmPassword.text
                )
            }

            Button {
                text: "Quay lại đăng nhập"
                flat: true
                Layout.alignment: Qt.AlignHCenter
                onClicked: page.backToLoginRequested()
            }
        }
    }
}
