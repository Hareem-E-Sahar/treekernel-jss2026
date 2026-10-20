# RQ1 figure: MAP per clone type over the 10 replicate query sets (box plots, ggplot2).
#
# usage: Rscript paper/rq1_boxplot.R   -> paper/figures/rq1_map_by_type.pdf
# Input: results/replicates/per_replicate.tsv (eval/replicates.py). Box = IQR and median, whiskers = min-max
# (no outliers drawn: 10 values per box). Colours as in paper/make_assets.py (Okabe-Ito).
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(here)

types <- c("T1", "T2", "VST3", "ST3", "MT3")
methods <- c("STK", "SSTK", "PTK", "BM25", "CodeBERT zs", "CodeBERT ft")
colours <- c("STK" = "#0072B2", "SSTK" = "#56B4E9", "PTK" = "#D55E00", "BM25" = "#555555",
             "CodeBERT zs" = "#CC79A7", "CodeBERT ft" = "#009E73")

rep <- read.delim(file.path(root, "results/replicates/per_replicate.tsv"), check.names = FALSE) |>
  mutate(method = sub("^D ", "", method)) |>
  filter(method %in% methods) |>
  pivot_longer(all_of(types), names_to = "type", values_to = "map") |>
  mutate(type = factor(type, levels = types), method = factor(method, levels = methods))
n_rep <- n_distinct(rep$seed)

# whiskers at min and max: compute the five numbers directly
stats <- rep |>
  group_by(type, method) |>
  summarise(ymin = min(map), lower = quantile(map, 0.25), middle = median(map),
            upper = quantile(map, 0.75), ymax = max(map), .groups = "drop")

dodge <- position_dodge(width = 0.85)
p <- ggplot(stats, aes(x = type, fill = method, colour = method)) +
  geom_boxplot(aes(ymin = ymin, lower = lower, middle = middle, upper = upper, ymax = ymax),
               stat = "identity", position = dodge, width = 0.75, linewidth = 0.25,
               median.colour = "black", median.linewidth = 0.4, key_glyph = "polygon") +   # black median: visible on flat boxes
  annotate("text", x = 1, y = 0.975, label = "all 1.000", size = 2.1, colour = "#555555", family = "serif") +
  scale_fill_manual(values = colours, name = NULL) +
  scale_colour_manual(values = colours, guide = "none") +
  scale_y_continuous(limits = c(0.5, 1.0), breaks = seq(0.5, 1.0, 0.1), expand = expansion(add = c(0, 0.01))) +
  labs(x = NULL, y = sprintf("MAP (%d query sets)", n_rep)) +
  guides(fill = guide_legend(ncol = 3, byrow = FALSE, keywidth = unit(7, "pt"), keyheight = unit(7, "pt"))) +
  theme_classic(base_size = 8, base_family = "serif") +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey85"),
        legend.position = "inside", legend.position.inside = c(0.01, 0.01), legend.justification = c(0, 0),
        legend.background = element_blank(), legend.text = element_text(size = 7),
        legend.key.spacing.x = unit(4, "pt"), legend.key.spacing.y = unit(1.5, "pt"), axis.text = element_text(size = 7, colour = "black"),
        axis.line = element_line(linewidth = 0.3), axis.ticks = element_line(linewidth = 0.3))

ggsave(file.path(root, "paper/figures/rq1_map_by_type.pdf"), p, width = 3.4, height = 2.3, units = "in",
       device = cairo_pdf)
cat("figure rq1_map_by_type.pdf\n")
