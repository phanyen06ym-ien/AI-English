import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: page
    signal createAccountRequested()

    function canSubmit() {
        if (!authController)
            return false
        return !authController.loading
            && username.text.trim().length > 0
            && password.text.length > 0
    }

    function submitLogin() {
        if (!canSubmit()) {
            if (authController)
                authController.login(username.text, password.text)
            return
        }
        console.log("LoginPage submitLogin called for username:", username.text.trim())
        authController.login(username.text, password.text)
    }

    Rectangle {
        anchors.fill: parent
        color: "#FAFAFA"
    }

    Card {
        width: 440
        height: 430
        anchors.centerIn: parent
        z: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 14

            Label {
                text: "AI-English"
                color: "#222222"
                font.family: "Segoe UI"
                font.pixelSize: 30
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Label {
                text: "Đăng nhập để tiếp tục"
                color: "#777777"
                font.family: "Segoe UI"
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
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
                Keys.onReturnPressed: password.forceActiveFocus()
            }

            PasswordField {
                id: password
                placeholderText: "Mật khẩu"
                Layout.fillWidth: true
                Keys.onReturnPressed: page.submitLogin()
            }

            Label {
                text: authController ? authController.statusMessage : ""
                visible: authController && authController.statusMessage.length > 0
                color: authController && authController.statusMessage.indexOf("thành công") >= 0 ? "#2D7D46" : "#B94C3D"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            PrimaryButton {
                id: loginButton
                text: authController && authController.loading ? "Đang đăng nhập..." : "Đăng nhập"
                enabled: page.canSubmit()
                Layout.fillWidth: true
                onClicked: page.submitLogin()
            }

            Button {
                text: "Tạo tài khoản"
                flat: true
                Layout.alignment: Qt.AlignHCenter
                onClicked: page.createAccountRequested()
            }
        }
    }

    Component.onCompleted: username.forceActiveFocus()
}
