import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property int maxCount: {
        var m = 1
        for (var i = 0; i < statsController.categoryBreakdown.length; i++) {
            m = Math.max(m, statsController.categoryBreakdown[i].count)
        }
        return m
    }

    Connections {
        target: statsController
        function onStatsChanged() {
            content.opacity = 0
            fadeAnim.restart()
        }
    }

    NumberAnimation {
        id: fadeAnim
        target: content
        property: "opacity"
        to: 1
        duration: 260
        easing.type: Easing.OutCubic
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                radius: 14
                color: "#ffffff"
                border.color: "#f1e3d3"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 4

                    Text { text: "Tổng lượt nhận diện"; color: "#a4988a"; font.pixelSize: 13 }
                    Text { text: statsController.total; color: "#3f3628"; font.pixelSize: 28; font.bold: true }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                radius: 14
                color: "#ffffff"
                border.color: "#f1e3d3"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 4

                    Text { text: "Từ vựng riêng biệt"; color: "#a4988a"; font.pixelSize: 13 }
                    Text { text: statsController.distinctWords; color: "#3f3628"; font.pixelSize: 28; font.bold: true }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                radius: 14
                color: "#ffffff"
                border.color: "#f1e3d3"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 6

                    Text { text: "Từ vựng đã học"; color: "#a4988a"; font.pixelSize: 13 }
                    Text {
                        text: statsController.vocabLearned + " / " + statsController.vocabTotal
                        color: "#3f3628"
                        font.pixelSize: 22
                        font.bold: true
                    }
                    ProgressBar {
                        Layout.fillWidth: true
                        from: 0
                        to: statsController.vocabTotal
                        value: statsController.vocabLearned
                        Behavior on value { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 14
            color: "#ffffff"
            border.color: "#f1e3d3"
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Text {
                    text: "Phân loại theo chủ đề"
                    color: "#3f3628"
                    font.pixelSize: 15
                    font.bold: true
                }

                Repeater {
                    model: statsController.categoryBreakdown

                    delegate: RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: modelData.category
                            color: "#5f5546"
                            font.pixelSize: 13
                            Layout.preferredWidth: 110
                            elide: Text.ElideRight
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 14
                            radius: 7
                            color: "#f6ead9"

                            Rectangle {
                                height: parent.height
                                radius: 7
                                color: "#f97316"
                                width: parent.width * (modelData.count / root.maxCount)
                                Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
                            }
                        }

                        Text {
                            text: modelData.count
                            color: "#a4988a"
                            font.pixelSize: 12
                            Layout.preferredWidth: 24
                        }
                    }
                }

                Text {
                    visible: statsController.categoryBreakdown.length === 0
                    text: "Chưa có dữ liệu thống kê."
                    color: "#a4988a"
                    font.pixelSize: 13
                }
            }
        }
    }
}
