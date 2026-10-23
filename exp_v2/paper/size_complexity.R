# exp_v2 paper figures for the size and complexity analysis (box plots, ggplot2).
#
# usage: Rscript exp_v2/paper/size_complexity.R
#   -> exp_v2/paper/figures/size_complexity_rq1.pdf   mean over the five clone types: nP@5, nP@10, MRR, MAP
#      exp_v2/paper/figures/size_complexity_rq2.pdf   functional:                     nP@5, nP@10, MRR, MAP@R
# Input: exp_v2/results/size_complexity/per_seed.tsv (exp_v2/eval/size_complexity.py), one value per seed and group.
# geom_boxplot with its defaults, as in exp_v2/paper/figures.R; same colours.
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(dirname(here))
out <- file.path(here, "figures")
dir.create(out, showWarnings = FALSE)

methods <- c("STK", "SSTK", "PTK", "BM25", "CodeBERT zs", "CodeBERT ft")
colours <- c("STK" = "#0072B2", "SSTK" = "#56B4E9", "PTK" = "#D55E00", "BM25" = "#555555",
             "CodeBERT zs" = "#CC79A7", "CodeBERT ft" = "#009E73")
groups <- c("small", "large", "low", "high")
glabels <- c("small\n(LOC ≤ 6)", "large\n(LOC ≥ 10)", "low\n(McCabe ≤ 10)", "high\n(McCabe > 10)")

ps <- read.delim(file.path(root, "exp_v2/results/size_complexity/per_seed.tsv"), check.names = FALSE) |>
  filter(group %in% groups, method %in% methods) |>
  mutate(group = factor(group, levels = groups, labels = glabels), method = factor(method, levels = methods))
n_seed <- n_distinct(ps$seed)

base_theme <- theme_classic(base_size = 8, base_family = "serif") +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey85"),
        axis.text = element_text(size = 7, colour = "black"), axis.line = element_line(linewidth = 0.3),
        axis.ticks = element_line(linewidth = 0.3), strip.background = element_blank(),
        strip.text = element_text(size = 8, face = "bold"), legend.text = element_text(size = 7),
        panel.spacing = unit(8, "pt"))

plot_groups <- function(measure_, metrics, name) {
  d <- ps |> filter(measure == measure_, metric %in% metrics) |> mutate(metric = factor(metric, levels = metrics))
  p <- ggplot(d, aes(x = group, y = value, fill = method, colour = method)) +
    geom_boxplot(position = position_dodge(width = 0.85), width = 0.75, linewidth = 0.25, outlier.size = 0.5,
                 outlier.stroke = 0.3, median.colour = "black", median.linewidth = 0.4, key_glyph = "polygon") +
    geom_vline(xintercept = 2.5, linewidth = 0.2, colour = "grey60", linetype = "dashed") +
    facet_wrap(~metric, nrow = 2, scales = "free_y") +
    scale_fill_manual(values = colours, name = NULL) +
    scale_colour_manual(values = colours, guide = "none") +
    labs(x = NULL, y = sprintf("value over %d seeds", n_seed)) +
    guides(fill = guide_legend(nrow = 1, keywidth = unit(7, "pt"), keyheight = unit(7, "pt"))) +
    base_theme + theme(legend.position = "top", legend.margin = margin(0, 0, -4, 0),
                       axis.text.x = element_text(size = 6.5, lineheight = 0.9))
  ggsave(file.path(out, name), p, width = 7.0, height = 4.2, units = "in", device = cairo_pdf)
  cat("figure", name, "\n")
}
plot_groups("mean5", c("nP@5", "nP@10", "MRR", "MAP"), "size_complexity_rq1.pdf")
plot_groups("functional", c("nP@5", "nP@10", "MRR", "MAP@R"), "size_complexity_rq2.pdf")
