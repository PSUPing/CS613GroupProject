import argparse
import sys, os

import numpy as np
import pylab as pl

from sklearn.externals import joblib
from sklearn.decomposition import PCA, KernelPCA, TruncatedSVD

#### To run, put this into command line: python pred_setA1.py -d ./cs613_grcomp_s14/ -id 1

if __name__ == '__main__':
    
    try:
        parser = argparse.ArgumentParser(description='baseline for predicting labels')

        parser.add_argument('-d',
                            default='.',
                            help='Directory with datasets in SVMLight format')

        parser.add_argument('-id', type=int,
                            choices=[1,2,3],
                            help='Dataset id')

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

        args = parser.parse_args()

        n_features = 100 ## dataset id = 3
        if args.id == 1:
            n_features = 253659
        elif args.id == 2:
            n_features = 200
        
        fname_trn = os.path.join(args.d, "dt%d.%s.svm" % (args.id, "trn"))
        fname_vld = os.path.join(args.d, "dt%d.%s.svm" % (args.id, "vld"))
        fname_tst = os.path.join(args.d, "dt%d.%s.svm" % (args.id, "tst"))

        fname_vld_lbl = os.path.join(args.d, "dt%d.%s.lbl" % (args.id, "vld"))
        fname_tst_lbl = os.path.join(args.d, "dt%d.%s.lbl" % (args.id, "tst"))

        fname_vld_pred = os.path.join(args.d, "dt%d.%s.pred" % (args.id, "vld"))
        fname_tst_pred = os.path.join(args.d, "dt%d.%s.pred" % (args.id, "tst"))
        
        for fn in (fname_trn, fname_vld, fname_tst):
            if not os.path.isfile(fn):
                print("Missing dataset file: %s " % (fn,))
                sys.exit(1)
        
        ### reading labels
        from sklearn.datasets import dump_svmlight_file, load_svmlight_file
        data_trn, lbl_trn = load_svmlight_file(fname_trn, n_features=n_features, zero_based=True)
        data_vld, lbl_vld = load_svmlight_file(fname_vld, n_features=n_features, zero_based=True)
        data_tst, lbl_tst = load_svmlight_file(fname_tst, n_features=n_features, zero_based=True)
        
        print("Files loaded")
# Start here for potential changes
        ### perform grid search using validation samples
        from sklearn.grid_search import ParameterGrid
        from sklearn.svm import LinearSVC, SVC, SVR, NuSVR
        from sklearn.metrics import mean_squared_error, accuracy_score
        from sklearn.linear_model import SGDClassifier, MultiTaskLasso, PassiveAggressiveClassifier
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.hmm import MultinomialHMM
        from sklearn.lda import LDA

        dt1_grid = [{'alpha': [0.0001, 0.00001, 0.000001, 0.0000001, 0.00000001, 0.000000001, 0.0000000001],
                     'loss' : ['hinge', 'log', 'modified_huber', 'perceptron']}]

#        dt1_grid = [{'C': [1e-1, 1e0, 1e1, 1e2, 1e3]}]

      #  dt2_grid = [{'kernel': ['rbf'], 'C': [1.0, 100.0, 10000.0],
       #              'gamma': [0.1, 1.0, 10.0]}]
        dt2_grid = [{'C': [0.1,1.0, 100.0, 10000.0],'n_iter':[1,5,4]}]


        dt3_grid = [{'kernel': ['rbf'], 'C': [1.0, 100.0],
                     'gamma': [0.1, 1.0, 10.0]}]
#        dt3_grid = [{'alpha': [ 0.0001, 0.00001,0.000001]}]

        grids = (None, dt1_grid, dt2_grid, dt3_grid)
        classifiers = (None, SGDClassifier, PassiveAggressiveClassifier, NuSVR)
#        classifiers = (None, LinearSVC, SVC, SVR)
        metrics = (None, accuracy_score, accuracy_score, mean_squared_error)
        str_formats = (None, "%d", "%d", "%.6f")
        #LinearSVC(penalty='l2', loss='l2', dual=True, tol=0.0001, C=1.0,

# Potential changes End

        grid_obj=grids[args.id]
        cls_obj=classifiers[args.id]
        metric_obj=metrics[args.id]
        
        best_param = None
        best_score = None
        best_svc = None

        if (args.id == 1):
            from sklearn.kernel_approximation import AdditiveChi2Sampler
            chi = AdditiveChi2Sampler()
            trn_data = chi.fit_transform(data_trn, lbl_trn) 
            vld_data = chi.transform(data_vld)
            tst_data = chi.transform(data_tst)
        elif (args.id == 2):
            trn_data = data_trn.todense()
            vld_data = data_vld.todense()
            tst_data = data_tst.todense()
        else:
            pca = PCA()
            pca = joblib.load("dt_combined.sqw.pca")
            trn_data = pca.inverse_transform(data_trn.todense())
            vld_data = pca.inverse_transform(data_vld.todense())
            tst_data = pca.inverse_transform(data_tst.todense())

        for one_param in ParameterGrid(grid_obj):
            cls = cls_obj(**one_param)
            cls.fit(trn_data, lbl_trn)
            one_score = metric_obj(lbl_vld, cls.predict(vld_data))

            print ("param=%s, score=%.6f" % (repr(one_param),one_score))
            
            if ( best_score is None or 
                 (args.id < 3 and best_score < one_score) or
                 (args.id == 3 and best_score > one_score) ):
                best_param = one_param
                best_score = one_score
                best_svc = cls
            
        pred_vld = best_svc.predict(vld_data)
        pred_tst = best_svc.predict(tst_data)
        
        print ("Best score for vld: %.6f" % (metric_obj(lbl_vld, pred_vld),))
        print ("Best score for tst: %.6f" % (metric_obj(lbl_tst, pred_tst),))
        
        np.savetxt(fname_vld_pred, pred_vld, delimiter='\n', fmt=str_formats[args.id])
        np.savetxt(fname_tst_pred, pred_tst, delimiter='\n', fmt=str_formats[args.id])
        
        np.savetxt(fname_vld_lbl, lbl_vld, delimiter='\n', fmt=str_formats[args.id])
        np.savetxt(fname_tst_lbl, lbl_tst, delimiter='\n', fmt=str_formats[args.id])
    except Exception, exc:
        import traceback
        print('Exception was raised in %s of %s: %s \n %s ' % (__name__, __file__, str(exc), ''.join(traceback.format_exc())))