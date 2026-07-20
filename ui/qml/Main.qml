import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: window
    width: 1280
    height: 760
    minimumWidth: 1040
    minimumHeight: 640
    visible: true
    title: "AI-English"
    color: "#FAFAFA"
    font.family: "Segoe UI"

    property int currentPage: 0
    property bool showRegister: false

    readonly property var pageTitles: [
        "Trang chủ",
        "Camera",
        "Lịch sử",
        "Thống kê",
        "Tài khoản"
    ]

    Connections {
        target: authController

        function onIsLoggedInChanged(loggedIn) {
            if (loggedIn) {
                window.currentPage = 0
                window.showRegister = false
            } else {
                window.currentPage = 0
            }
        }
    }

    Loader {
        anchors.fill: parent
        active: authController ? !authController.isLoggedIn : true
        sourceComponent: window.showRegister ? registerPage : loginPage
    }

    Component {
        id: loginPage
        LoginPage {
            onCreateAccountRequested: window.showRegister = true
        }
    }

    Component {
        id: registerPage
        RegisterPage {
            onBackToLoginRequested: window.showRegister = false
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        visible: authController ? authController.isLoggedIn : false

        Rectangle {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            color: "#FFFFFF"
            border.color: "#E8E8E8"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 8

                Label {
                    text: "AI-English"
                    color: "#222222"
                    font.pixelSize: 25
                    font.bold: true
                    Layout.fillWidth: true
                    Layout.preferredHeight: 56
                    verticalAlignment: Text.AlignVCenter
                }

                Divider { Layout.fillWidth: true }

                SidebarButton {
                    text: "🏠  Trang chủ"
                    selected: window.currentPage === 0
                    onClicked: window.currentPage = 0
                }

                SidebarButton {
                    text: "📷  Camera"
                    selected: window.currentPage === 1
                    onClicked: window.currentPage = 1
                }

                SidebarButton {
                    text: "📖  Lịch sử"
                    selected: window.currentPage === 2
                    onClicked: {
                        window.currentPage = 2
                        historyController.refresh()
                    }
                }

                SidebarButton {
                    text: "📊  Thống kê"
                    selected: window.currentPage === 3
                    onClicked: {
                        window.currentPage = 3
                        statsController.refresh()
                    }
                }

                SidebarButton {
                    text: "👤  Tài khoản"
                    selected: window.currentPage === 4
                    onClicked: window.currentPage = 4
                }

                Item { Layout.fillHeight: true }

                Divider { Layout.fillWidth: true }

                SidebarButton {
                    text: "↩  Đăng xuất"
                    selected: false
                    onClicked: authController.logout()
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 70
                color: "#FAFAFA"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 28
                    spacing: 0

                    Label {
                        text: window.pageTitles[window.currentPage]
                        color: "#222222"
                        font.pixelSize: 24
                        font.bold: true
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        verticalAlignment: Text.AlignVCenter
                    }

                    Divider { Layout.fillWidth: true }
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.currentPage

                HomePage {}
                CameraPage {}
                HistoryPage {}
                StatisticsPage {}
                AccountPage {}
            }
        }
    }
}
