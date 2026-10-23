# exp_v2 paper figures: corpus with false positives, 10 replicate query sets (box plots, ggplot2).
#
# usage: Rscript exp_v2/paper/figures.R
#   -> exp_v2/paper/figures/rq1_metrics.pdf            RQ1 per clone type: nP@5, nP@10, MRR, MAP
#      exp_v2/paper/figures/rq2_metrics.pdf            RQ2 functional:     nP@5, nP@10, MRR, MAP@R
#      exp_v2/paper/figures/rq4_fusion_rq1.pdf         RQ4, PTK fusions, mean over the five types: nP@5, nP@10, MRR, MAP
#      exp_v2/paper/figures/rq4_fusion_rq2.pdf         RQ4, STK fusions, functional:               nP@5, nP@10, MRR, MAP@R
# Input: exp_v2/results/fp/per_replicate_metrics.tsv (exp_v2/eval/replicate_metrics.py), one value per replicate.
# geom_boxplot with its defaults: box = IQR and median, whiskers to the most extreme value within 1.5 IQR, points beyond.
# Colours as in paper/make_assets.py (Okabe-Ito).
suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
root <- dirname(dirname(here))
out <- file.path(here, "figures")
dir.create(out, showWarnings = FALSE)

types <- c("T1", "T2", "VST3", "ST3", "MT3")
methods <- c("STK", "SSTK", "PTK", "BM25", "CodeBERT zs", "CodeBERT ft")
colours <- c("STK" = "#0072B2", "SSTK" = "#56B4E9", "PTK" = "#D55E00", "BM25" = "#555555",
             "CodeBERT zs" = "#CC79A7", "CodeBERT ft" = "#009E73")

rep <- read.delim(file.path(root, "exp_v2/results/fp/per_replicate_metrics.tsv"), check.names = FALSE) |>
  mutate(method = sub("^D ", "", method))
n_rep <- n_distinct(rep$seed)

base_theme <- theme_classic(base_size = 8, base_family = "serif") +
  theme(panel.grid.major.y = element_line(linewidth = 0.2, colour = "grey85"),
        axis.text = element_text(size = 7, colour = "black"), axis.line = element_line(linewidth = 0.3),
        axis.ticks = element_line(linewidth = 0.3), strip.background = element_blank(),
        strip.text = element_text(size = 8, face = "bold"), legend.text = element_text(size = 7),
        panel.spacing = unit(8, "pt"))
box <- function(...) geom_boxplot(..., linewidth = 0.25, outlier.size = 0.5, outlier.stroke = 0.3,
                                  median.colour = "black", median.linewidth = 0.4, key_glyph = "polygon")
ylab <- sprintf("value over %d replicate query sets", n_rep)
save <- function(p, name, w, h) {
  ggsave(file.path(out, name), p, width = w, height = h, units = "in", device = cairo_pdf)
  cat("figure", name, "\n")
}

# ---- RQ1: per clone type, the six methods
m1 <- c("nP@5", "nP@10", "MRR", "MAP")
d1 <- rep |>
  filter(measure %in% types, metric %in% m1, method %in% methods) |>
  mutate(measure = factor(measure, levels = types), method = factor(method, levels = methods),
         metric = factor(metric, levels = m1))
p <- ggplot(d1, aes(x = measure, y = value, fill = method, colour = method)) +
  box(position = position_dodge(width = 0.85), width = 0.75) +
  facet_wrap(~metric, nrow = 2, scales = "free_y") +
  scale_fill_manual(values = colours, name = NULL) +
  scale_colour_manual(values = colours, guide = "none") +
  labs(x = NULL, y = ylab) +
  guides(fill = guide_legend(nrow = 1, keywidth = unit(7, "pt"), keyheight = unit(7, "pt"))) +
  base_theme + theme(legend.position = "top", legend.margin = margin(0, 0, -4, 0))
save(p, "rq1_metrics.pdf", 7.0, 4.2)

# ---- RQ2: functional, the six methods
m2 <- c("nP@5", "nP@10", "MRR", "MAP@R")
d2 <- rep |>
  filter(measure == "functional", metric %in% m2, method %in% methods) |>
  mutate(method = factor(method, levels = methods), metric = factor(metric, levels = m2))
p <- ggplot(d2, aes(x = method, y = value, fill = method, colour = method)) +
  box(width = 0.65) +
  facet_wrap(~metric, nrow = 2, scales = "free_y") +
  scale_fill_manual(values = colours, guide = "none") +
  scale_colour_manual(values = colours, guide = "none") +
  scale_x_discrete(labels = c("STK", "SSTK", "PTK", "BM25", "CB zs", "CB ft")) +
  labs(x = NULL, y = ylab) +
  base_theme + theme(axis.text.x = element_text(size = 6.5, angle = 40, hjust = 1))
save(p, "rq2_metrics.pdf", 3.5, 3.6)

# ---- RQ4: each fusion next to its two components
fusion_plot <- function(kernel, measure_, metrics, name) {
  comps <- c(kernel, "BM25", "CodeBERT ft")
  fus <- c(paste0(kernel, "+BM25 wsum"), paste0(kernel, "+BM25 RRF"),
           paste0(kernel, "+CodeBERT ft wsum"), paste0(kernel, "+CodeBERT ft RRF"))
  ticks <- c(kernel, "BM25", "CB ft", "+BM25\nwsum", "+BM25\nRRF", "+CB ft\nwsum", "+CB ft\nRRF")
  d <- rep |>
    filter(measure == measure_, metric %in% metrics, method %in% c(comps, fus)) |>
    mutate(tick = factor(ticks[match(method, c(comps, fus))], levels = ticks),
           fill = case_when(method %in% comps ~ method, grepl("wsum", method) ~ "weighted sum", TRUE ~ "RRF"),
           metric = factor(metric, levels = metrics))
  fills <- c(colours[comps], "weighted sum" = "white", "RRF" = "grey80")
  p <- ggplot(d, aes(x = tick, y = value, fill = fill)) +
    box(width = 0.6, colour = "black") +
    geom_vline(xintercept = 3.5, linewidth = 0.2, colour = "grey60", linetype = "dashed") +
    facet_wrap(~metric, nrow = 2, scales = "free_y") +
    scale_fill_manual(values = fills, breaks = c("weighted sum", "RRF"), name = paste0(kernel, " fused by")) +
    labs(x = NULL, y = ylab) +
    guides(fill = guide_legend(nrow = 1, keywidth = unit(7, "pt"), keyheight = unit(7, "pt"))) +
    base_theme + theme(legend.position = "top", legend.margin = margin(0, 0, -4, 0),
                       legend.title = element_text(size = 7), axis.text.x = element_text(size = 6.5, lineheight = 0.9))
  save(p, name, 7.0, 3.8)
}
fusion_plot("PTK", "mean5", m1, "rq4_fusion_rq1.pdf")
fusion_plot("STK", "functional", m2, "rq4_fusion_rq2.pdf")
