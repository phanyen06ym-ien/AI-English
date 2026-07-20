import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: page
    property var statistics: ({})

    Connections {
        target: statsController

        function onStatsChanged(stats) {
            page.statistics = stats
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        Card {
            Layout.fillWidth: true
            Layout.preferredHeight: 180

            RowLayout {
                anchors.fill: parent
                anchors.margins: 26
                spacing: 22

                Rectangle {
                    Layout.preferredWidth: 92
                    Layout.preferredHeight: 92
                    radius: 24
                    color: "#FBE4CA"

                    Label {
                        anchors.centerIn: parent
                        text: "AI"
                        color: "#222222"
                        font.family: "Segoe UI"
                        font.pixelSize: 30
                        font.bold: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: "AI-English"
                        color: "#222222"
                        font.family: "Segoe UI"
                        font.pixelSize: 34
                        font.bold: true
                    }

                    Label {
                        text: "Hệ thống nhận dạng vật thể hỗ trợ học tiếng Anh"
                        color: "#777777"
                        font.family: "Segoe UI"
                        font.pixelSize: 16
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: page.width > 760 ? 3 : 1
            columnSpacing: 16
            rowSpacing: 16

            StatCard {
                title: "Số lần nhận diện"
                value: String(page.statistics.totalDetections || 0)
                helper: "Từ lịch sử nhận diện"
                Layout.fillWidth: true
            }

            StatCard {
                title: "Số từ đã học"
                value: String(page.statistics.uniqueWords || 0)
                helper: "Số từ khác nhau"
                Layout.fillWidth: true
            }

            StatCard {
                title: "Lần sử dụng gần nhất"
                value: "N/A"
                helper: "Backend chưa cung cấp dữ liệu này"
                Layout.fillWidth: true
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 12

                SectionTitle { text: "Bắt đầu nhanh" }

                Label {
                    text: "Sử dụng Camera để nhận diện qua webcam hoặc tải ảnh, sau đó xem lại kết quả trong Lịch sử và Thống kê."
                    color: "#777777"
                    font.family: "Segoe UI"
                    font.pixelSize: 15
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
