import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import AIEnglish 1.0
import "components"

Item {
    id: page

    property bool hasMedia: false
    property string activeMode: "image"
    property string statusText: "Sẵn sàng."
    property var imageResults: imageController ? imageController.detections : []
    property var imageRelatedWords: imageController ? imageController.relatedWords : []
    property var imageClusterWords: imageController ? imageController.clusterWords : []
    property var webcamResults: webcamController ? webcamController.detections : []
    property var webcamRelatedWords: webcamController ? webcamController.relatedWords : []
    property var webcamClusterWords: webcamController ? webcamController.clusterWords : []

    property var currentResults: activeMode === "webcam" ? webcamResults : imageResults
    property var currentRelatedWords: activeMode === "webcam" ? webcamRelatedWords : imageRelatedWords
    property var currentClusterWords: activeMode === "webcam" ? webcamClusterWords : imageClusterWords

    Connections {
        target: imageController

        function onImageChanged(image) {
            page.activeMode = "image"
            page.hasMedia = true
            preview.setImage(image)
        }

        function onResultsChanged(results) {
            page.activeMode = "image"
            page.imageResults = results
            historyController.refresh()
            statsController.refresh()
        }

        function onRelatedWordsChanged(words) {
            page.imageRelatedWords = words
        }

        function onClusterWordsChanged(words) {
            page.imageClusterWords = words
        }

        function onStatusChanged(message) {
            page.statusText = message
        }
    }

    Connections {
        target: webcamController

        function onFrameChanged(frame) {
            page.activeMode = "webcam"
            page.hasMedia = true
            preview.setImage(frame)
        }

        function onStatusChanged(message) {
            page.statusText = message
        }

        function onResultsChanged(results) {
            page.webcamResults = results
        }

        function onHistorySaved() {
            historyController.refresh()
            statsController.refresh()
        }

        function onRelatedWordsChanged(words) {
            page.webcamRelatedWords = words
        }

        function onClusterWordsChanged(words) {
            page.webcamClusterWords = words
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 18

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 560
            spacing: 14

            Card {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Item {
                    anchors.fill: parent
                    anchors.margins: 14

                    VideoItem {
                        id: preview
                        anchors.fill: parent
                        visible: page.hasMedia
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: !page.hasMedia
                        text: "VIDEO"
                        color: "#777777"
                        font.family: "Segoe UI"
                        font.pixelSize: 28
                        font.bold: true
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                PrimaryButton {
                    text: webcamController && webcamController.running ? "Đang bật" : "Bật Camera"
                    enabled: webcamController && !webcamController.running
                    onClicked: webcamController.start()
                }

                PrimaryButton {
                    text: "Tắt Camera"
                    enabled: webcamController && webcamController.running
                    onClicked: webcamController.stop()
                }

                PrimaryButton {
                    text: "Tải ảnh"
                    enabled: imageController && !imageController.busy
                    onClicked: imageController.chooseImage()
                }

                PrimaryButton {
                    text: imageController && imageController.busy ? "Đang nhận diện..." : "Nhận diện"
                    enabled: imageController && !imageController.busy && imageController.selectedImagePath.length > 0
                    onClicked: imageController.detectSelectedImage()
                }

                Label {
                    text: page.statusText
                    color: page.statusText.indexOf("Không") >= 0 || page.statusText.indexOf("Vui lòng") >= 0 ? "#B94C3D" : "#777777"
                    font.family: "Segoe UI"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }

        Card {
            Layout.preferredWidth: Math.max(320, page.width * 0.28)
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                SectionTitle {
                    text: page.activeMode === "webcam" ? "Kết quả realtime" : "Kết quả ảnh"
                }
                Divider { Layout.fillWidth: true }

                ListView {
                    id: resultList
                    Layout.fillWidth: true
                    Layout.preferredHeight: 250
                    clip: true
                    model: page.currentResults

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 92
                        radius: 10
                        color: "#FAFAFA"
                        border.color: "#E8E8E8"

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3

                                Label {
                                    text: modelData.english || "N/A"
                                    color: "#222222"
                                    font.family: "Segoe UI"
                                    font.pixelSize: 17
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: modelData.vietnamese || "N/A"
                                    color: "#777777"
                                    font.family: "Segoe UI"
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: "Độ tin cậy: " + (Number(modelData.confidence || 0) * 100).toFixed(2) + "%"
                                    color: "#777777"
                                    font.family: "Segoe UI"
                                    font.pixelSize: 12
                                }
                            }

                            Button {
                                text: "▶"
                                implicitWidth: 36
                                implicitHeight: 32
                                visible: page.activeMode === "image"
                                onClicked: imageController.speak(modelData.english)
                            }
                        }
                    }
                }

                Label {
                    visible: page.currentResults.length === 0
                    text: page.activeMode === "image"
                          ? "Tải ảnh rồi bấm Nhận diện"
                          : "Chưa phát hiện vật thể"
                    color: "#777777"
                    font.family: "Segoe UI"
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                }

                SectionTitle { text: "Từ gợi ý" }
                Divider { Layout.fillWidth: true }

                ListView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    clip: true
                    model: page.currentRelatedWords

                    delegate: Label {
                        width: ListView.view.width
                        text: modelData.english + " - " + modelData.vietnamese
                        color: "#222222"
                        font.family: "Segoe UI"
                        padding: 6
                        wrapMode: Text.WordWrap
                    }
                }

                SectionTitle { text: "Cùng nhóm" }
                Divider { Layout.fillWidth: true }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: page.currentClusterWords

                    delegate: Label {
                        width: ListView.view.width
                        text: modelData.english + " - " + modelData.vietnamese
                        color: "#222222"
                        font.family: "Segoe UI"
                        padding: 6
                        wrapMode: Text.WordWrap
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: page.currentRelatedWords.length === 0 && page.currentClusterWords.length === 0
                        text: "Gợi ý sẽ cập nhật sau khi có kết quả nhận diện."
                        color: "#777777"
                        font.family: "Segoe UI"
                        width: parent.width - 20
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }
}
