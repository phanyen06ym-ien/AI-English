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
        spacing: 16

        GridLayout {
            Layout.fillWidth: true
            columns: page.width > 850 ? 4 : 2
            columnSpacing: 16
            rowSpacing: 16

            StatCard {
                title: "Tổng lượt nhận diện"
                value: String(page.statistics.totalDetections || 0)
                Layout.fillWidth: true
            }

            StatCard {
                title: "Tổng số từ"
                value: String(page.statistics.uniqueWords || 0)
                Layout.fillWidth: true
            }

            StatCard {
                title: "Độ tin cậy trung bình"
                value: ((page.statistics.averageConfidence || 0) * 100).toFixed(2) + "%"
                helper: "Confidence trung bình của các kết quả nhận diện"
                Layout.fillWidth: true
            }

            StatCard {
                title: "Từ xuất hiện nhiều nhất"
                value: page.statistics.mostDetectedWord || page.statistics.mostCommonWord || "N/A"
                Layout.fillWidth: true
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                SectionTitle { text: "Danh sách thống kê" }
                Divider { Layout.fillWidth: true }

                ListView {
                    id: categoryList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: Object.keys(page.statistics.categories || {})

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 48
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            spacing: 12

                            Label {
                                text: modelData
                                color: "#222222"
                                font.family: "Segoe UI"
                                Layout.preferredWidth: 180
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 10
                                radius: 5
                                color: "#F4F4F4"

                                Rectangle {
                                    width: parent.width * Math.min(1, ((page.statistics.categories || {})[modelData] || 0) / Math.max(1, page.statistics.totalDetections || 1))
                                    height: parent.height
                                    radius: 5
                                    color: "#F6B26B"
                                }
                            }

                            Label {
                                text: String((page.statistics.categories || {})[modelData] || 0)
                                color: "#777777"
                                horizontalAlignment: Text.AlignRight
                                Layout.preferredWidth: 60
                            }
                        }
                    }
                }

                Label {
                    visible: categoryList.count === 0
                    text: "Chưa có dữ liệu thống kê"
                    color: "#777777"
                    font.family: "Segoe UI"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }
        }
    }
}
