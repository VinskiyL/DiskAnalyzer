#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QVBoxLayout>          // Добавьте этот include
#include <QtCharts/QChartView>  // Для QChartView
#include <QtCharts/QPieSeries>  // Для демо-диаграммы

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    // Создаем и устанавливаем layout для widgetChart
    QVBoxLayout *layout = new QVBoxLayout(ui->widgetChart);
    layout->setContentsMargins(0, 0, 0, 0);  // Убираем отступы

    // Создаем и настраиваем chartView
    QChartView *chartView = new QChartView(ui->widgetChart);
    chartView->setRenderHint(QPainter::Antialiasing);

    // Добавляем демо-диаграмму
    QPieSeries *series = new QPieSeries();
    series->append("Used", 75);
    series->append("Free", 25);

    QChart *chart = new QChart();
    chart->addSeries(series);
    chart->setTitle("Disk Usage");

    chartView->setChart(chart);
    layout->addWidget(chartView);  // Добавляем chartView в layout
}

MainWindow::~MainWindow()
{
    delete ui;
}

